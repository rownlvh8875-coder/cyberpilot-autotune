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
  printf("CPB_EXIT ok=%d\n", ok);
  fflush(stdout);
  syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
          LINUX_REBOOT_CMD_RESTART, NULL);
  for (;;) pause();
}

static void need(int yes)
{
  if (!yes) {
    printf("CPB_UNAVAILABLE errno=%d\n", errno);
    if (getpid() != 1) _exit(2);
    finish(0);
  }
}

static void workload(const char *mode)
{
  int fd = syscall(SYS_memfd_create, "post-arm", MFD_CLOEXEC);
  need(fd == 7);
  need(dup3(fd, 41, O_CLOEXEC) == 41);
  int expected = !strcmp(mode, "TASK_FAIL") ? EAGAIN :
    (!strcmp(mode, "CONSTRUCTOR_FAIL") || !strcmp(mode, "ALLOC_FAIL")) ? ENOMEM : 0;
  pid_t child = fork();
  if (expected) {
    need(child == -1 && errno == expected);
  } else {
    need(child >= 0);
    if (child == 0) {
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
  need(getpid() == 1);
  need(mount("proc", "/proc", "proc", 0, NULL) == 0);
  char mode[32] = {0}, seed[32], arm[32];
  int input = open("/case", O_RDONLY);
  need(input >= 0 && read(input, mode, sizeof(mode)-1) > 0);
  close(input);
  const char *names[] = {"NORMAL", "SEED_LOSS", "SMALL_BUFFER", "SEED_FAIL",
    "UNSEEDED_OFD", "RESEED_REJECTED", "EARLY_ARM_REJECTED", "CONSTRUCTOR_FAIL",
    "TASK_FAIL", "ALLOC_FAIL"};
  int known = 0;
  for (unsigned int i = 0; i < sizeof(names)/sizeof(names[0]); i++)
    known |= !strcmp(mode, names[i]);
  need(known);
  int n = snprintf(seed, sizeof(seed), "seed %s\n", mode);
  int a = snprintf(arm, sizeof(arm), "arm %s\n", mode);
  need(n > 0 && n < (int)sizeof(seed) && a > 0 && a < (int)sizeof(arm));
  int control = open("/proc/cpbootstrap", O_WRONLY);
  int snapshot = open("/proc/cpbootstrap", O_RDONLY);
  need(control == 3 && snapshot == 4);
  int first = syscall(SYS_memfd_create, "fixed-equal", MFD_CLOEXEC);
  int second = syscall(SYS_memfd_create, "fixed-equal", MFD_CLOEXEC);
  need(first == 5 && second == 6);
  need(write(first, "same-data", 9) == 9 && write(second, "same-data", 9) == 9);
  need(lseek(first, 0, SEEK_SET) == 0 && lseek(second, 0, SEEK_SET) == 0);
  need(dup3(first, 40, O_CLOEXEC) == 40);
  if (!strcmp(mode, "EARLY_ARM_REJECTED"))
    need(write(control, arm, a) == -1 && errno == EINVAL);
  int forked = strcmp(mode, "SEED_FAIL") != 0;
  if (!forked) {
    need(write(control, seed, n) == -1 && errno == EIO);
  } else {
    need(write(control, seed, n) == n);
    if (!strcmp(mode, "RESEED_REJECTED"))
      need(write(control, seed, n) == -1 && errno == EBUSY);
    need(write(control, arm, a) == a);
    pid_t root = fork();
    need(root >= 0);
    if (root == 0) workload(mode);
    int status = -1;
    need(waitpid(root, &status, 0) == root);
    need(WIFEXITED(status) && WEXITSTATUS(status) == 0);
  }
  need(write(control, "stop\n", 5) == 5);
  printf("CPB_DRIVER ok=1 forked=%d\n", forked);
  char buffer[8192];
  ssize_t got;
  while ((got = read(snapshot, buffer, sizeof(buffer))) > 0)
    need(write(1, buffer, got) == got);
  need(got == 0);
  close(snapshot); close(control);
  need(close(first) == 0 && close(second) == 0 && close(40) == 0);
  finish(1);
}
