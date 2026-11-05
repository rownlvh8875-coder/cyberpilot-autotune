#define main direct_supervisor_main
#include "supervisor.c"
#undef main
#include <dirent.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/random.h>
#include <sys/stat.h>
#include <sys/vfs.h>

#define CGROUP2_MAGIC 0x63677270
static int read_small(int fd, char *out, size_t cap) {
  ssize_t n = read(fd, out, cap - 1);
  if (n <= 0 || (size_t)n >= cap - 1) return -1;
  out[n] = 0; return 0;
}
static int read_at_small(int dir, const char *name, char *out, size_t cap) {
  int fd = openat(dir, name, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
  if (fd < 0) return -1;
  int r = read_small(fd, out, cap);
  if (close_once(fd)) r = -1;
  return r;
}
static int membership(pid_t pid, char *out, size_t cap) {
  char name[64], text[2048];
  int n = snprintf(name, sizeof name, "/proc/%ld/cgroup", (long)pid);
  if (n <= 0 || (size_t)n >= sizeof name) return -1;
  int fd = open(name, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
  if (fd < 0) return -1;
  int r = read_small(fd, text, sizeof text);
  close_once(fd);
  if (r || strncmp(text, "0::/", 4)) return -1;
  char *end = strchr(text, '\n');
  if (!end || end[1] || (size_t)(end - text - 3) >= cap) return -1;
  *end = 0;
  if (strstr(text + 3, "..")) return -1;
  strcpy(out, text + 3); return 0;
}
static int factory_service(const char *path) {
  const char *leaf = strrchr(path, '/');
  if (!leaf) return 0;
  ++leaf;
  const char *prefix = "native-e-domain-";
  size_t p = strlen(prefix);
  if (strncmp(leaf, prefix, p) || strlen(leaf) != p + 32 + 8) return 0;
  for (size_t i = p; i < p + 32; ++i)
    if (!((leaf[i] >= '0' && leaf[i] <= '9') || (leaf[i] >= 'a' && leaf[i] <= 'f'))) return 0;
  return !strcmp(leaf + p + 32, ".service");
}
static int open_parent(const char *path) {
  if (!factory_service(path)) return -1;
  int fd = open("/sys/fs/cgroup", O_RDONLY | O_DIRECTORY | O_CLOEXEC | O_NOFOLLOW);
  if (fd < 0) return -1;
  char copy[2048];
  if (strlen(path) >= sizeof copy) { close_once(fd); return -1; }
  strcpy(copy, path + 1);
  char *save = NULL;
  for (char *part = strtok_r(copy, "/", &save); part; part = strtok_r(NULL, "/", &save)) {
    if (!strcmp(part, ".") || !strcmp(part, "..")) { close_once(fd); return -1; }
    int next = openat(fd, part, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
    close_once(fd); fd = next;
    if (fd < 0 || uncertain) { close_once(fd); return -1; }
  }
  struct stat st;
  struct statfs fs;
  char type[64];
  if (fstat(fd, &st) || st.st_uid != geteuid() || fstatfs(fd, &fs) ||
      fs.f_type != CGROUP2_MAGIC || read_at_small(fd, "cgroup.type", type, sizeof type) ||
      strcmp(type, "domain\n")) { close_once(fd); return -1; }
  return fd;
}
static int original_D(int parent, int d, int anchor, const char *name) {
  if (uncertain) return 0;
  struct stat a, b, named;
  if (fstat(d, &a) || fstat(anchor, &b) ||
      fstatat(parent, name, &named, AT_SYMLINK_NOFOLLOW) ||
      !S_ISDIR(named.st_mode) || a.st_dev != b.st_dev || a.st_ino != b.st_ino ||
      a.st_dev != named.st_dev || a.st_ino != named.st_ino ||
      syscall(SYS_kcmp, getpid(), getpid(), 0, (unsigned long)d, (unsigned long)anchor) != 0) {
    uncertain = 1; return 0;
  }
  return 1;
}
static int exactly_child(int d, pid_t child) {
  char text[128], expected[64];
  if (uncertain || read_at_small(d, "cgroup.procs", text, sizeof text)) {
    uncertain = 1; return 0;
  }
  snprintf(expected, sizeof expected, "%ld\n", (long)child);
  if (strcmp(text, expected)) { uncertain = 1; return 0; }
  return 1;
}
static int no_descendants(int d) {
  char text[4096];
  unsigned seen = 0;
  if (uncertain || read_at_small(d, "cgroup.stat", text, sizeof text)) {
    uncertain = 1; return 0;
  }
  const char *keys[] = {"nr_descendants ", "nr_dying_descendants "};
  char *save = NULL;
  for (char *line = strtok_r(text, "\n", &save); line; line = strtok_r(NULL, "\n", &save)) {
    for (unsigned i = 0; i < 2; ++i) {
      size_t prefix = strlen(keys[i]);
      if (strncmp(line, keys[i], prefix)) continue;
      char *value = line + prefix, *end;
      if (*value < '0' || *value > '9' || (seen & (1u << i))) {
        uncertain = 1; return 0;
      }
      errno = 0;
      unsigned long number = strtoul(value, &end, 10);
      if (errno || *end || number != 0) { uncertain = 1; return 0; }
      seen |= 1u << i;
    }
  }
  if (seen != 3) { uncertain = 1; return 0; }
  return 1;
}
static int empty_D(int d) {
  char text[256];
  if (read_at_small(d, "cgroup.events", text, sizeof text)) return 0;
  return !strncmp(text, "populated 0\n", 12) || strstr(text, "\npopulated 0\n") != NULL;
}
static int worker_fds(pid_t child, const struct stat *data) {
  char name[96];
  snprintf(name, sizeof name, "/proc/%ld/fd", (long)child);
  DIR *dir = opendir(name);
  if (!dir) { uncertain = 1; return 0; }
  unsigned mask = 0;
  struct dirent *entry;
  int ok = 1;
  for (;;) {
    errno = 0;
    entry = readdir(dir);
    if (!entry) { if (errno) ok = 0; break; }
    if (!strcmp(entry->d_name, ".") || !strcmp(entry->d_name, "..")) continue;
    char *end;
    long n = strtol(entry->d_name, &end, 10);
    if (*end || n < 0 || n > 4 || (mask & (1u << n))) { ok = 0; break; }
    mask |= 1u << n;
    struct stat st;
    char target[128];
    snprintf(target, sizeof target, "/proc/%ld/fd/%ld", (long)child, n);
    if (stat(target, &st) || S_ISDIR(st.st_mode)) { ok = 0; break; }
    if (n <= 2 && !S_ISCHR(st.st_mode)) { ok = 0; break; }
    if (n == 3 && !S_ISSOCK(st.st_mode)) { ok = 0; break; }
    if (n == 4 && (st.st_dev != data->st_dev || st.st_ino != data->st_ino)) { ok = 0; break; }
  }
  if (closedir(dir)) uncertain = 1;
  if (!ok || mask != 31) uncertain = 1;
  return !uncertain;
}
static int open_fixed_worker(struct stat *info) {
  char path[PATH_MAX];
  ssize_t n = readlink("/proc/self/exe", path, sizeof path - 1);
  if (n <= 0 || (size_t)n >= sizeof path - 1) return -1;
  path[n] = 0;
  char *leaf = strrchr(path, '/');
  if (!leaf || strcmp(leaf + 1, "domain_supervisor")) return -1;
  *leaf = 0;
  int dir = open(path, O_DIRECTORY | O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
  if (dir < 0) return -1;
  int fd = openat(dir, "domain_worker", O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
  close_once(dir);
  if (fd < 0) return -1;
  if (uncertain || fstat(fd, info) || !S_ISREG(info->st_mode) ||
      info->st_uid != geteuid() || (info->st_mode & 06022) ||
      info->st_size <= 0 || info->st_size > 1024 * 1024) {
    close_once(fd); return -1;
  }
  return fd;
}
static int worker_image(pid_t child, const struct stat *expected) {
  char path[64];
  struct stat actual;
  snprintf(path, sizeof path, "/proc/%ld/exe", (long)child);
  return !stat(path, &actual) && actual.st_dev == expected->st_dev &&
    actual.st_ino == expected->st_ino;
}
static void birth_exec(int endpoint, int datafd, int executable, pid_t owner) {
  /* Native E trampoline is not worker image entry. Kernel exec closes ALL
     nonexported FDs before the fixed worker image begins. */
  int s = fcntl(endpoint, F_DUPFD_CLOEXEC, 10);
  int m = fcntl(datafd, F_DUPFD_CLOEXEC, 10);
  int x = fcntl(executable, F_DUPFD_CLOEXEC, 12);
  if (s < 0 || m < 0 || x < 0 || dup2(s, 3) < 0 || dup2(m, 4) < 0) _exit(31);
  if (syscall(SYS_close_range, 5u, ~0u, 4u)) _exit(32); /* CLOSE_RANGE_CLOEXEC */
  close(0);
  if (open("/dev/null", O_RDONLY) != 0 ||
      prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != owner) _exit(33);
  char *const argv[] = {"domain_worker", NULL};
  char *const env[] = {"LANG=C.UTF-8", NULL};
  syscall(SYS_execveat, x, "", argv, env, AT_EMPTY_PATH);
  _exit(34);
}
static int unavailable(const unsigned char *ctx, int err) {
  unsigned char raw[N + 4];
  memcpy(raw, ctx, N); raw[5] = 255;
  uint32_t e = htonl((uint32_t)err), n = htonl(N + 4);
  memcpy(raw + N, &e, 4);
  return write_all(0, &n, 4) || write_all(0, raw, sizeof raw);
}
static int report_D(const unsigned char *ctx) {
  unsigned char raw[N + 4];
  memcpy(raw, ctx, N); raw[5] = 5;
  uint32_t seq = htonl(4), bits = htonl(255), n = htonl(N + 4);
  memcpy(raw + 6, &seq, 4); memcpy(raw + N, &bits, 4);
  return write_all(0, &n, 4) || write_all(0, raw, sizeof raw);
}
static int wait_domain_original(int pidfd, int *killed) {
  struct pollfd p = {.fd = pidfd, .events = POLLIN};
  if (poll(&p, 1, 2000) != 1) return -1;
  siginfo_t info;
  memset(&info, 0, sizeof info);
  if (waitid(P_PIDFD, (id_t)pidfd, &info, WEXITED)) return -1;
  *killed = info.si_code == CLD_KILLED && info.si_status == SIGKILL;
  return 0;
}
int main(int argc, char **argv) {
  (void)argv;
  if (argc != 1 || geteuid() == 0) return 22;
  if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) || set_limit(RLIMIT_CORE, 0) ||
      set_limit(RLIMIT_CPU, 2) || set_limit(RLIMIT_AS, 64 * 1024 * 1024) ||
      set_limit(RLIMIT_FSIZE, 4096) || set_limit(RLIMIT_NOFILE, 32)) return 22;
  struct timeval timeout = {.tv_sec = 2};
  if (setsockopt(0, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof timeout)) return 22;
  unsigned char msg[MAX_FRAME], ctx[N], random[16];
  size_t size;
  if (frame(0, msg, &size) || size != N || memcmp(msg, "NEL1", 4) ||
      msg[4] != 1 || msg[5] != 1 || memcmp(msg + 6, "\0\0\0\0", 4)) return 20;
  memcpy(ctx, msg, N);
  int workerfd = -1, parent = -1, d = -1, anchor = -1, datafd = -1, pidfd = -1, pair[2] = {-1,-1};
  int made = 0, removed = 0, wait_attempted = 0, reaped = 0, kill_attempted = 0, result = 20;
  pid_t child = -1;
  char parent_path[2048], child_path[2112], actual[2048], name[48];
  if (membership(getpid(), parent_path, sizeof parent_path) ||
      (parent = open_parent(parent_path)) < 0) {
    unavailable(ctx, EACCES); result = 78; goto done;
  }
  if (getrandom(random, sizeof random, 0) != sizeof random) {
    unavailable(ctx, EIO); result = 78; goto done;
  }
  strcpy(name, "owned-d-");
  for (unsigned i = 0; i < sizeof random; ++i) snprintf(name + 8 + 2 * i, 3, "%02x", random[i]);
  if (mkdirat(parent, name, 0700)) { unavailable(ctx, errno); result = 78; goto done; }
  made = 1;
  d = openat(parent, name, O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC);
  if (d < 0 || (anchor = fcntl(d, F_DUPFD_CLOEXEC, 3)) < 0 ||
      !original_D(parent, d, anchor, name)) { uncertain = 1; goto done; }
  snprintf(child_path, sizeof child_path, "%s/%s", parent_path, name);
  datafd = memfd_create("internal-d-fixed", MFD_CLOEXEC | MFD_ALLOW_SEALING);
  struct stat data_info;
  if (datafd < 0 || write(datafd, fixture, sizeof fixture - 1) != sizeof fixture - 1 ||
      fcntl(datafd, F_ADD_SEALS, 15) || fstat(datafd, &data_info) ||
      socketpair(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC, 0, pair)) goto done;
  struct stat worker_info;
  workerfd = open_fixed_worker(&worker_info);
  if (workerfd < 0) goto done;
  struct clone_args args;
  memset(&args, 0, sizeof args);
  args.flags = CLONE_PIDFD | CLONE_INTO_CGROUP;
  args.pidfd = (uint64_t)(uintptr_t)&pidfd;
  args.exit_signal = SIGCHLD; args.cgroup = (uint64_t)d;
  pid_t owner = getpid();
  long born = syscall(SYS_clone3, &args, sizeof args);
  if (born < 0) { unavailable(ctx, errno); result = 78; goto done; }
  if (!born) birth_exec(pair[1], datafd, workerfd, owner);
  child = (pid_t)born;
  close_once(pair[1]); pair[1] = -1;
  unsigned char ready;
  if (exact(pair[0], &ready, 1, 0, now_ms() + 2000) || ready != 'R' ||
      membership(child, actual, sizeof actual) || strcmp(actual, child_path) ||
      !worker_image(child, &worker_info) || !worker_fds(child, &data_info) || !exactly_child(d, child) || !no_descendants(d)) {
    uncertain = 1; goto done;
  }
  if (emit(0, ctx, 2, 1) || frame(0, msg, &size) || !matches(msg, size, ctx, 3, 2) ||
      frame(0, msg, &size) != 1 || write_all(pair[0], "G", 1)) goto done;
  if (exact(pair[0], &ready, 1, 0, now_ms() + 2000) || ready != 'D') goto done;
  if (!original_D(parent, d, anchor, name) || !exactly_child(d, child) || !no_descendants(d) ||
      membership(getpid(), actual, sizeof actual) || strcmp(actual, parent_path)) {
    uncertain = 1; goto done;
  }
  struct pollfd active = {.fd = pidfd, .events = POLLIN};
  if (poll(&active, 1, 0) != 0) goto done;
  int killfd = openat(d, "cgroup.kill", O_WRONLY | O_NOFOLLOW | O_CLOEXEC);
  if (killfd < 0) goto done;
  kill_attempted = 1;
  ssize_t wrote = write(killfd, "1\n", 2);
  close_once(killfd);
  if (wrote != 2) { uncertain = 1; goto done; }
  int killed;
  wait_attempted = 1;
  if (wait_domain_original(pidfd, &killed)) { uncertain = 1; goto done; }
  reaped = 1;
  if (!killed) goto done;
  if (uncertain || !empty_D(d) || !original_D(parent, d, anchor, name)) {
    uncertain = 1; goto done;
  }
  if (unlinkat(parent, name, AT_REMOVEDIR)) { uncertain = 1; goto done; }
  removed = 1;
  if (emit(0, ctx, 4, 3) || report_D(ctx)) goto done;
  result = 0;
done:
  if (pidfd >= 0 && !wait_attempted) {
    if (!kill_attempted &&
        syscall(SYS_pidfd_send_signal, pidfd, SIGKILL, NULL, 0) && errno != ESRCH) uncertain = 1;
    wait_attempted = 1;
    int ignored;
    if (wait_original(pidfd, &ignored)) uncertain = 1; else reaped = 1;
  }
  if (made && !removed && !uncertain) {
    if ((child < 0 || reaped) && d >= 0 && anchor >= 0 && empty_D(d) &&
        original_D(parent, d, anchor, name)) {
      if (unlinkat(parent, name, AT_REMOVEDIR)) uncertain = 1;
      else removed = 1;
    } else uncertain = 1;
  }
  close_once(pidfd); close_once(pair[0]); close_once(pair[1]); close_once(datafd);
  close_once(workerfd); close_once(anchor); close_once(d); close_once(parent); close_once(0);
  return uncertain ? 21 : result;
}
