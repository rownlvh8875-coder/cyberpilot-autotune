#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/sched.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* Fixed synthetic E. No executable/path/PID/FD/unit/payload argument API.
 * clone3's original pidfd identifies only its direct child, NOT a cgroup D.
 */
#define N 50
#define MAX_FRAME 512
static int uncertain = 0;
static const char fixture[] = "NATIVE_E_FIXED_SYNTHETIC_V1\n";

static int close_once(int fd) {
  if (fd < 0) return 0;
  if (close(fd) < 0) { uncertain = 1; return -1; }
  return 0;
}
static int64_t now_ms(void) {
  struct timespec t;
  if (clock_gettime(CLOCK_MONOTONIC, &t)) return -1;
  return (int64_t)t.tv_sec * 1000 + t.tv_nsec / 1000000;
}
static int exact(int fd, unsigned char *out, size_t n, int boundary, int64_t end) {
  size_t used = 0;
  while (used < n) {
    int64_t left = end - now_ms();
    if (left <= 0 || left > 2000) return -1;
    struct pollfd p = {.fd = fd, .events = POLLIN};
    int r = poll(&p, 1, (int)left);
    if (r <= 0) return -1;
    unsigned char ancillary[CMSG_SPACE(32 * sizeof(int))];
    struct iovec iov = {.iov_base = out + used, .iov_len = n - used};
    struct msghdr msg = {0};
    msg.msg_iov = &iov; msg.msg_iovlen = 1;
    msg.msg_control = ancillary; msg.msg_controllen = sizeof ancillary;
    ssize_t got = recvmsg(fd, &msg, MSG_CMSG_CLOEXEC);
    int extra = (msg.msg_flags & (MSG_CTRUNC | MSG_TRUNC)) != 0;
    if (got < 0) return -1;
    for (struct cmsghdr *h = CMSG_FIRSTHDR(&msg); h; h = CMSG_NXTHDR(&msg, h)) {
      extra = 1;
      if (h->cmsg_level == SOL_SOCKET && h->cmsg_type == SCM_RIGHTS &&
          h->cmsg_len >= CMSG_LEN(0)) {
        size_t count = (h->cmsg_len - CMSG_LEN(0)) / sizeof(int);
        for (size_t i = 0; i < count; ++i) {
          int received;
          memcpy(&received, (unsigned char *)CMSG_DATA(h) + i * sizeof(int), sizeof received);
          close_once(received);
        }
      }
    }
    if (extra) return -1;
    if (!got) return boundary && !used ? 1 : -1;
    used += (size_t)got;
  }
  return 0;
}
/* 1 = clean stream EOF; 0 = message; -1 = invalid/timeout/partial. */
static int frame(int fd, unsigned char *out, size_t *size) {
  unsigned char prefix[4];
  int64_t end = now_ms() + 2000;
  int r = exact(fd, prefix, 4, 1, end);
  if (r) return r;
  uint32_t n;
  memcpy(&n, prefix, 4); n = ntohl(n);
  if (!n || n > MAX_FRAME) return -1;
  *size = n;
  return exact(fd, out, n, 0, end);
}
static int write_all(int fd, const void *data, size_t n) {
  const unsigned char *p = data;
  while (n) {
    ssize_t r = send(fd, p, n, MSG_NOSIGNAL);
    if (r <= 0) return -1;
    p += r; n -= (size_t)r;
  }
  return 0;
}
static int emit(int fd, const unsigned char *ctx, unsigned stage, unsigned seq) {
  unsigned char msg[N];
  uint32_t s = htonl(seq), len = htonl(N);
  memcpy(msg, ctx, N); msg[5] = (unsigned char)stage; memcpy(msg + 6, &s, 4);
  return write_all(fd, &len, 4) || write_all(fd, msg, N) ? -1 : 0;
}
static int matches(const unsigned char *msg, size_t size, const unsigned char *ctx,
                   unsigned stage, unsigned seq) {
  unsigned char expected[N];
  uint32_t s = htonl(seq);
  memcpy(expected, ctx, N); expected[5] = (unsigned char)stage;
  memcpy(expected + 6, &s, 4);
  return size == N && memcmp(msg, expected, N) == 0;
}
static int set_limit(int type, rlim_t max) {
  struct rlimit limit = {.rlim_cur = max, .rlim_max = max};
  return setrlimit(type, &limit);
}
static int wait_original(int pidfd, int *status) {
  struct pollfd p = {.fd = pidfd, .events = POLLIN};
  if (poll(&p, 1, 2000) != 1) return -1;
  siginfo_t info;
  memset(&info, 0, sizeof info);
  if (waitid(P_PIDFD, (id_t)pidfd, &info, WEXITED)) return -1;
  *status = info.si_code == CLD_EXITED ? info.si_status : 128 + info.si_status;
  return 0;
}
static void worker(int endpoint, int datafd, pid_t owner) {
  /* Relocate only E-created capabilities. No directory descriptor or ambient credentials. */
  int socket_copy = fcntl(endpoint, F_DUPFD_CLOEXEC, 10);
  int data_copy = fcntl(datafd, F_DUPFD_CLOEXEC, 10);
  if (socket_copy < 0 || data_copy < 0 ||
      dup2(socket_copy, 3) < 0 || dup2(data_copy, 4) < 0) _exit(31);
  if (syscall(SYS_close_range, 5u, ~0u, 0)) _exit(32);
  close(0);
  if (open("/dev/null", O_RDONLY | O_CLOEXEC) != 0) _exit(33);
  if (prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != owner) _exit(34);
  unsigned char go[1];
  if (exact(3, go, 1, 0, now_ms() + 2000) || go[0] != 'G') _exit(35);
  char actual[sizeof fixture];
  if (fcntl(4, F_GET_SEALS) != (F_SEAL_SEAL | F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_WRITE) ||
      pread(4, actual, sizeof fixture - 1, 0) != (ssize_t)(sizeof fixture - 1) ||
      memcmp(actual, fixture, sizeof fixture - 1)) _exit(36);
  if (write_all(3, "D", 1)) _exit(37);
  if (close(3) || close(4)) _exit(38);
  _exit(0);
}
int main(int argc, char **argv) {
  (void)argv;
  if (argc != 1 || geteuid() == 0) return 22;
  if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) ||
      set_limit(RLIMIT_CORE, 0) || set_limit(RLIMIT_CPU, 2) ||
      set_limit(RLIMIT_AS, 64 * 1024 * 1024) || set_limit(RLIMIT_FSIZE, 4096) ||
      set_limit(RLIMIT_NOFILE, 32)) return 22;
  struct timeval timeout = {.tv_sec = 2, .tv_usec = 0};
  if (setsockopt(0, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof timeout)) return 22;
  unsigned char msg[MAX_FRAME], ctx[N];
  size_t size = 0;
  int result = 20, pidfd = -1, datafd = -1, pair[2] = {-1, -1}, wait_attempted = 0;
  if (frame(0, msg, &size) || size != N || memcmp(msg, "NEL1", 4) ||
      msg[4] != 1 || msg[5] != 1 ||
      memcmp(msg + 6, "\0\0\0\0", 4)) goto done;
  memcpy(ctx, msg, N);
  if (!(datafd = memfd_create("native-e-synthetic", MFD_CLOEXEC | MFD_ALLOW_SEALING)) ||
      datafd < 0) goto done;
  if (write(datafd, fixture, sizeof fixture - 1) != (ssize_t)(sizeof fixture - 1) ||
      fcntl(datafd, F_ADD_SEALS, F_SEAL_SEAL | F_SEAL_SHRINK | F_SEAL_GROW | F_SEAL_WRITE) ||
      socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, pair)) goto done;
  struct clone_args args;
  memset(&args, 0, sizeof args);
  args.flags = CLONE_PIDFD;
  args.pidfd = (uint64_t)(uintptr_t)&pidfd;
  args.exit_signal = SIGCHLD;
  pid_t owner = getpid();
  long child = syscall(SYS_clone3, &args, sizeof args);
  if (child < 0) {
    unsigned char unavailable[N + 4];
    memcpy(unavailable, ctx, N); unavailable[5] = 255;
    uint32_t err = htonl((uint32_t)errno), length = htonl(N + 4);
    memcpy(unavailable + N, &err, 4);
    if (write_all(0, &length, 4) || write_all(0, unavailable, sizeof unavailable))
      goto done;
    result = 78; goto done;
  }
  if (!child) worker(pair[1], datafd, owner);
  /* pidfd was installed atomically by clone3. Never reacquire by PID or name. */
  close_once(pair[1]); pair[1] = -1;
  if (emit(0, ctx, 2, 1) || frame(0, msg, &size) ||
      !matches(msg, size, ctx, 3, 2)) goto done;
  /* Require EOF after exactly one RUN. No extra request can execute. */
  if (frame(0, msg, &size) != 1 || write_all(pair[0], "G", 1)) goto done;
  unsigned char finished;
  if (exact(pair[0], &finished, 1, 0, now_ms() + 2000) || finished != 'D') goto done;
  int status = -1;
  wait_attempted = 1;
  if (wait_original(pidfd, &status)) { uncertain = 1; goto done; }
  if (status || uncertain) goto done;
  if (emit(0, ctx, 4, 3) || emit(0, ctx, 5, 4)) goto done;
  result = 0;
done:
  if (pidfd >= 0 && !wait_attempted) {
    if (syscall(SYS_pidfd_send_signal, pidfd, SIGKILL, NULL, 0) && errno != ESRCH)
      uncertain = 1;
    int ignored;
    if (wait_original(pidfd, &ignored)) uncertain = 1;
  }
  close_once(pidfd); close_once(datafd); close_once(pair[0]); close_once(pair[1]);
  close_once(0);
  return uncertain ? 21 : result;
}
