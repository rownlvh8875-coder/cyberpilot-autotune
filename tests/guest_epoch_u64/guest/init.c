#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/memfd.h>
#include <linux/reboot.h>
#include <stdio.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

static void finish(int ok)
{
  printf("CPR2_EXIT ok=%d\n", ok);
  fflush(stdout);
  syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
          LINUX_REBOOT_CMD_RESTART, NULL);
  for (;;) pause();
}

static void need(int yes)
{
  if (!yes) {
    printf("CPR2_UNAVAILABLE errno=%d\n", errno);
    if (getpid() != 1) _exit(2);
    finish(0);
  }
}

static void workload(const char *mode)
{
  int fd = syscall(SYS_memfd_create, "post-arm", MFD_CLOEXEC);
  need(fd == 7 && dup3(fd, 41, O_CLOEXEC) == 41);
  pid_t child = fork();
  if (!strcmp(mode, "CONSTRUCTOR_FAIL")) {
    need(child == -1 && errno == ENOMEM);
  } else {
    need(child >= 0);
    if (!child) {
      if (close(fd) != 0 || close(41) != 0) _exit(2);
      _exit(0);
    }
    int status = -1;
    need(waitpid(child, &status, 0) == child);
    need(WIFEXITED(status) && WEXITSTATUS(status) == 0);
  }
  need(close(fd) == 0 && close(41) == 0);
  _exit(0);
}

int main(void)
{
  int console = open("/dev/console", O_RDWR);
  if (console >= 0) {
    dup2(console, 0); dup2(console, 1); dup2(console, 2);
    if (console > 2) close(console);
  }
  setvbuf(stdout, NULL, _IONBF, 0);
  need(getpid() == 1 && mount("proc", "/proc", "proc", 0, NULL) == 0);
  char mode[32] = {0}, seed[40], arm[40];
  int input = open("/case", O_RDONLY);
  need(input >= 0 && read(input, mode, sizeof(mode)-1) > 0);
  close(input);
  const char *names[] = {"NORMAL", "SEED_LOSS", "SMALL_BUFFER", "UNSEEDED_OFD",
    "CONSTRUCTOR_FAIL", "SNAPSHOT_LOSS", "POINTER_LOSS"};
  int known = 0;
  for (unsigned int i = 0; i < sizeof(names)/sizeof(names[0]); i++)
    known |= !strcmp(mode, names[i]);
  need(known);
  int n = snprintf(seed, sizeof(seed), "seed %s\n", mode);
  int a = snprintf(arm, sizeof(arm), "arm %s\n", mode);
  need(n > 0 && n < (int)sizeof(seed) && a > 0 && a < (int)sizeof(arm));
  int control = open("/proc/cptagread", O_WRONLY);
  int snapshot = open("/proc/cptagread", O_RDONLY);
  need(control == 3 && snapshot == 4);
  int first = syscall(SYS_memfd_create, "fixed-equal", MFD_CLOEXEC);
  int second = syscall(SYS_memfd_create, "fixed-equal", MFD_CLOEXEC);
  need(first == 5 && second == 6);
  need(write(first, "same-data", 9) == 9 && write(second, "same-data", 9) == 9);
  need(dup3(first, 40, O_CLOEXEC) == 40);
  need(write(control, seed, n) == n && write(control, arm, a) == a);
  pid_t root = fork();
  need(root >= 0);
  if (!root) workload(mode);
  int status = -1;
  need(waitpid(root, &status, 0) == root);
  need(WIFEXITED(status) && WEXITSTATUS(status) == 0);
  need(write(control, "stop\n", 5) == 5);
  printf("CPR2_DRIVER ok=1\n");
  char buffer[8192];
  ssize_t got;
  while ((got = read(snapshot, buffer, sizeof(buffer))) > 0)
    need(write(1, buffer, got) == got);
  need(got == 0);
  close(snapshot); close(control);
  need(close(first) == 0 && close(second) == 0 && close(40) == 0);
  finish(1);
}
