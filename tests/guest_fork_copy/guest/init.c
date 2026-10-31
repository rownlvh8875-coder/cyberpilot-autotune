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
  printf("CPC_EXIT ok=%d\n", ok);
  fflush(stdout);
  syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
          LINUX_REBOOT_CMD_RESTART, NULL);
  for (;;) pause();
}

static void need(int yes)
{
  if (!yes) {
    printf("CPC_UNAVAILABLE errno=%d\n", errno);
    if (getpid() != 1) _exit(2);
    finish(0);
  }
}

static void workload(const char *mode)
{
  int fd = syscall(SYS_memfd_create, "fixed-per-slot-copy", MFD_CLOEXEC);
  need(fd == 5);
  need(dup3(fd, 40, 0) == 40);
  need(fcntl(40, F_SETFD, FD_CLOEXEC) == 0);
  need(dup3(fd, 40, O_CLOEXEC) == 40);
  int expected = !strcmp(mode, "TASK_FAIL") ? EAGAIN :
    (!strcmp(mode, "CONSTRUCTOR_FAIL") || !strcmp(mode, "ALLOC_FAIL")) ? ENOMEM : 0;
  pid_t child = fork();
  if (expected) {
    need(child == -1 && errno == expected);
  } else {
    need(child >= 0);
    if (child == 0) {
      if (close(fd) != 0 || close(40) != 0) _exit(2);
      _exit(0);
    }
    int status = -1;
    need(waitpid(child, &status, 0) == child);
    need(WIFEXITED(status) && WEXITSTATUS(status) == 0);
  }
  need(close(fd) == 0 && close(40) == 0);
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
  char mode[32] = {0}, arm[32];
  int input = open("/case", O_RDONLY);
  need(input >= 0 && read(input, mode, sizeof(mode)-1) > 0);
  close(input);
  need(!strcmp(mode,"NORMAL") || !strcmp(mode,"READ_LOSS") ||
       !strcmp(mode,"SMALL_BUFFER") || !strcmp(mode,"CONSTRUCTOR_FAIL") ||
       !strcmp(mode,"TASK_FAIL") || !strcmp(mode,"ALLOC_FAIL"));
  int n = snprintf(arm, sizeof(arm), "arm %s\n", mode);
  need(n > 0 && n < (int)sizeof(arm));
  int control = open("/proc/cpcopy", O_WRONLY);
  int snapshot = open("/proc/cpcopy", O_RDONLY);
  need(control == 3 && snapshot == 4);
  need(write(control, arm, n) == n);
  pid_t root = fork();
  need(root >= 0);
  if (root == 0) workload(mode);
  int status = -1;
  need(waitpid(root, &status, 0) == root);
  need(WIFEXITED(status) && WEXITSTATUS(status) == 0);
  need(write(control, "stop\n", 5) == 5);
  printf("CPC_DRIVER ok=1 root=0 child=0\n");
  char buffer[8192];
  ssize_t got;
  while ((got = read(snapshot, buffer, sizeof(buffer))) > 0)
    need(write(1, buffer, got) == got);
  need(got == 0);
  close(snapshot); close(control);
  finish(1);
}
