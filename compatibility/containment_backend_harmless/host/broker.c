/* Actual USER_NOTIF read-only emulation, executed exclusively in the fixed guest. */
#define _GNU_SOURCE
#include "common.h"
#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/openat2.h>
#include <linux/seccomp.h>
#include <sched.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/uio.h>
#include <unistd.h>

#define ALLOW_NR(number) BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, number, 0, 1), \
                        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)
#define NOTIFY_NR(number) BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, number, 0, 1), \
                         BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_USER_NOTIF)

static pid_t bound_pid;
static const char *bound_fixture;
static struct broker_result *observation;

int install_payload_filter(void)
{
  struct sock_filter rules[] = {
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
    BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000U, 0, 1),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
    NOTIFY_NR(SYS_open), NOTIFY_NR(SYS_openat), NOTIFY_NR(SYS_openat2), NOTIFY_NR(SYS_creat),
    ALLOW_NR(SYS_read), ALLOW_NR(SYS_write), ALLOW_NR(SYS_close), ALLOW_NR(SYS_exit),
    ALLOW_NR(SYS_exit_group), ALLOW_NR(SYS_brk), ALLOW_NR(SYS_mmap), ALLOW_NR(SYS_munmap),
    ALLOW_NR(SYS_mprotect), ALLOW_NR(SYS_fstat), ALLOW_NR(SYS_newfstatat),
    ALLOW_NR(SYS_getpid), ALLOW_NR(SYS_gettid), ALLOW_NR(SYS_futex),
    ALLOW_NR(SYS_clock_gettime), ALLOW_NR(SYS_rt_sigreturn), ALLOW_NR(SYS_pause),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
  };
  struct sock_fprog program = {(unsigned short)(sizeof(rules) / sizeof(rules[0])), rules};
  return syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, SECCOMP_FILTER_FLAG_NEW_LISTENER, &program);
}

static int restrict_broker(int listener)
{
  /* The worker has no policy/control FDs. Its ioctl permission is confined to
   * the already-bound notification listener, not arbitrary kernel objects. */
  struct sock_filter rules[] = {
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_ioctl, 0, 4),
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, args[0])),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (unsigned int)listener, 0, 1),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
    ALLOW_NR(SYS_process_vm_readv), ALLOW_NR(SYS_openat2), ALLOW_NR(SYS_fstat),
    ALLOW_NR(SYS_fcntl), ALLOW_NR(SYS_close), ALLOW_NR(SYS_exit), ALLOW_NR(SYS_exit_group),
    ALLOW_NR(SYS_sched_yield), ALLOW_NR(SYS_brk), ALLOW_NR(SYS_mmap), ALLOW_NR(SYS_munmap),
    ALLOW_NR(SYS_mprotect), ALLOW_NR(SYS_rt_sigreturn),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | EPERM),
  };
  struct sock_fprog program = {(unsigned short)(sizeof(rules) / sizeof(rules[0])), rules};
  if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) return -1;
  return syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, 0, &program);
}

void broker_bind(pid_t pid, const char *fixture_id, struct broker_result *result)
{
  bound_pid = pid; bound_fixture = fixture_id; observation = result;
}

static int copied_from_child(uint64_t address, void *destination, size_t length)
{
  struct iovec local = {destination, length};
  struct iovec remote = {(void *)(uintptr_t)address, length};
  return process_vm_readv(bound_pid, &local, 1, &remote, 1, 0) == (ssize_t)length;
}

int broker_readonly_main(int listener_fd, int approved_root_fd, int report_fd)
{
  (void)report_fd;
  if (restrict_broker(listener_fd)) return 80;
  struct seccomp_notif request = {0};
  if (ioctl(listener_fd, SECCOMP_IOCTL_NOTIF_RECV, &request)) return 81;
  observation->request_id = request.id;
  int error = 0;
  struct open_how how = {0};
  uint64_t path_pointer = 0;
  int dirfd = AT_FDCWD;
  if (request.pid != (unsigned int)bound_pid ||
      ioctl(listener_fd, SECCOMP_IOCTL_NOTIF_ID_VALID, &request.id)) error = EPERM;
  if (!error) {
    switch (request.data.nr) {
      case SYS_open:
        path_pointer = request.data.args[0]; how.flags = request.data.args[1]; break;
      case SYS_openat:
        dirfd = (int)request.data.args[0]; path_pointer = request.data.args[1];
        how.flags = request.data.args[2]; break;
      case SYS_openat2:
        dirfd = (int)request.data.args[0]; path_pointer = request.data.args[1];
        if (request.data.args[3] != sizeof(how) ||
            !copied_from_child(request.data.args[2], &how, sizeof(how))) error = EINVAL;
        break;
      default: error = EPERM;
    }
  }
  if (!error && dirfd != AT_FDCWD) error = EPERM;
  if (!error && (how.flags & (O_PATH | O_CREAT | O_TRUNC | O_APPEND | O_WRONLY | O_RDWR))) error = EPERM;
  if (!error && ((how.flags & ~(uint64_t)O_CLOEXEC) || how.mode || how.resolve)) error = EINVAL;
  char path[256] = {0};
  if (!error && (!copied_from_child(path_pointer, path, sizeof(path)) ||
                 !memchr(path, 0, sizeof(path)) || !path[0])) error = EFAULT;
  if (!error && (!strcmp(path, "/dev/kfd") || !strcmp(path, "/dev/nvidiactl") ||
                 !strcmp(path, "/dev/nvidia-uvm") || !strcmp(path, "/dev/kgsl-3d0"))) error = EPERM;
  if (!error && (!strcmp(bound_fixture, "HF02") || !strcmp(bound_fixture, "HF03"))) {
    __atomic_store_n(&observation->copy_ready, 1, __ATOMIC_RELEASE);
    while (!__atomic_load_n(&observation->mutation_done, __ATOMIC_ACQUIRE)) sched_yield();
    observation->copied_path_used = !strcmp(path, "allowed");
  }
  int opened = -1;
  if (!error) {
    how.flags = O_RDONLY | O_CLOEXEC;
    how.resolve = RESOLVE_IN_ROOT | RESOLVE_NO_MAGICLINKS;
    observation->lookup_calls++;
    opened = syscall(SYS_openat2, approved_root_fd, path, &how, sizeof(how));
    if (opened < 0) error = errno;
  }
  if (!error) {
    struct stat object;
    if (fstat(opened, &object) || !S_ISREG(object.st_mode) ||
        object.st_ino != observation->expected_ino || object.st_dev != observation->expected_dev) {
      error = EPERM;
    } else {
      observation->object_matches = 1;
      observation->read_only = (fcntl(opened, F_GETFL) & O_ACCMODE) == O_RDONLY;
    }
  }
  observation->reply_errno = error;
  if (error) {
    struct seccomp_notif_resp reply = {.id=request.id, .error=-error, .flags=0};
    if (opened >= 0) close(opened);
    return ioctl(listener_fd, SECCOMP_IOCTL_NOTIF_SEND, &reply) ? 82 : 0;
  }
  struct seccomp_notif_addfd add = {.id=request.id, .flags=SECCOMP_ADDFD_FLAG_SEND,
      .srcfd=(unsigned int)opened, .newfd_flags=O_CLOEXEC};
  observation->addfd_result = ioctl(listener_fd, SECCOMP_IOCTL_NOTIF_ADDFD, &add);
  int saved = errno;
  close(opened);
  if (observation->addfd_result < 0) { observation->reply_errno = saved; return 83; }
  return 0;
}
