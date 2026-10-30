#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/memfd.h>
#include <linux/reboot.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static void finish(int ok)
{
  printf("CPL_EXIT ok=%d\n", ok);
  fflush(stdout);
  syscall(SYS_reboot, LINUX_REBOOT_MAGIC1, LINUX_REBOOT_MAGIC2,
          LINUX_REBOOT_CMD_RESTART, NULL);
  for (;;) pause();
}

static void need(int condition)
{
  if (!condition) {
    printf("CPL_UNAVAILABLE errno=%d\n", errno);
    finish(0);
  }
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
  char mode[32] = {0};
  int mode_fd = open("/case", O_RDONLY);
  need(mode_fd >= 0);
  ssize_t mode_n = read(mode_fd, mode, sizeof(mode) - 1);
  need(mode_n > 0);
  close(mode_fd);
  const char *arm = NULL;
  if (!strcmp(mode, "NORMAL")) arm = "arm normal\n";
  if (!strcmp(mode, "FORCED_LOSS")) arm = "arm fail\n";
  if (!strcmp(mode, "SMALL_BUFFER")) arm = "arm small\n";
  need(arm != NULL);
  int control = open("/proc/cplife", O_WRONLY);
  int snapshot = open("/proc/cplife", O_RDONLY);
  need(control >= 0 && snapshot >= 0);
  need(write(control, arm, strlen(arm)) == (ssize_t)strlen(arm));

  int fd = syscall(SYS_memfd_create, "fixed-raw-lifecycle", MFD_CLOEXEC);
  need(fd >= 0 && fd < 40);
  need(dup3(fd, 40, 0) == 40);
  need(fcntl(40, F_SETFD, FD_CLOEXEC) == 0);
  /* A real replacement of an occupied slot, without another OFD allocation. */
  need(dup3(fd, 40, O_CLOEXEC) == 40);
  pid_t child = fork();
  need(child >= 0);
  if (child == 0) {
    if (close(fd) != 0 || close(40) != 0) _exit(2);
    _exit(0);
  }
  int status = -1;
  need(waitpid(child, &status, 0) == child);
  need(WIFEXITED(status) && WEXITSTATUS(status) == 0);
  need(close(fd) == 0 && close(40) == 0);
  need(write(control, "stop\n", 5) == 5);
  printf("CPL_DRIVER ok=1 child=0\n");
  char buffer[4096];
  ssize_t n;
  while ((n = read(snapshot, buffer, sizeof(buffer))) > 0)
    need(write(1, buffer, n) == n);
  need(n == 0);
  close(snapshot); close(control);
  finish(1);
}
