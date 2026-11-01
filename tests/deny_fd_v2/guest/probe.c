/* Fixed harmless GUEST source only. Compile-only stage: NEVER host-execute. */
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <inttypes.h>
#include <limits.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/ptrace.h>
#include <sys/random.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#ifndef SOURCE_REVISION
#error A source-bound revision is mandatory
#endif
#ifndef SOURCE_MANIFEST_DIGEST
#error A pre-build source manifest digest is mandatory
#endif

_Static_assert(sizeof(int) == 4, "Int32 FD wire required");
static const char scope[] = "deny-fd-v2: fixed pre-exec inventory probe only\n";
static uint64_t sequence, previous_ns;
struct profile { const char *label; int subject; int installed[3]; int count; };
static const struct profile profiles[] = {
  {"DFD01", 0, {0, 3, 0}, 2}, {"DFD02", 0, {0, 0, 0}, 1},
  {"DFD03", 3, {0, 3, 0}, 2}, {"DFD04", 0, {0, 3, 4}, 3},
  {"DFD05", 0, {0, 0, 0}, 0}, {"DFD06", 0, {3, 0, 0}, 1}
};
struct snapshot {
  int fd[64], count, threads, nnp;
  unsigned uid, gid;
  uint64_t fd_seq[64], fd_time[64];
};

static int out(const char *kind, const char *format, ...)
{
  struct timespec t;
  if (sequence >= 1024 || clock_gettime(CLOCK_MONOTONIC, &t) || t.tv_sec < 0 ||
      t.tv_nsec < 0 || t.tv_nsec >= 1000000000L) return -1;
  if ((uint64_t)t.tv_sec > (UINT64_MAX - (uint64_t)t.tv_nsec) / 1000000000ULL) return -1;
  uint64_t ns = (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
  if (sequence && ns <= previous_ns) return -1; /* Never manufacture previous+1. */
  previous_ns = ns;
  sequence++;
  if (printf("DFD2 [%" PRIu64 ",%" PRIu64 ",\"%s\"", sequence, ns, kind) < 0) return -1;
  va_list args;
  va_start(args, format);
  int rc = vprintf(format, args);
  va_end(args);
  return rc < 0 || puts("]") == EOF || ferror(stdout) ? -1 : 0;
}

static int guest_guard(void)
{
  struct utsname u;
  if (geteuid() != 0 || uname(&u) || strcmp(u.machine, "x86_64") ||
      strcmp(u.release, "6.12.113+deb13-cloud-amd64")) return -1;
  if (strlen(SOURCE_REVISION) != 40 || strspn(SOURCE_REVISION, "0123456789abcdef") != 40 ||
      strlen(SOURCE_MANIFEST_DIGEST) != 64 ||
      strspn(SOURCE_MANIFEST_DIGEST, "0123456789abcdef") != 64) return -1;
  int fd = open("/etc/deny-fd-v2-scope", O_RDONLY | O_CLOEXEC);
  if (fd < 0) return -1;
  char bytes[128];
  ssize_t n = read(fd, bytes, sizeof(bytes));
  int closed = close(fd);
  return !closed && n == (ssize_t)strlen(scope) && !memcmp(bytes, scope, (size_t)n) ? 0 : -1;
}

static int inventory(pid_t child, struct snapshot *s, int publish)
{
  char path[80];
  snprintf(path, sizeof(path), "/proc/%d/fd", child);
  DIR *dir = opendir(path);
  if (!dir) return -1;
  s->count = 0;
  int result = -1;
  struct dirent *entry;
  errno = 0;
  while ((entry = readdir(dir))) {
    if (!strcmp(entry->d_name, ".") || !strcmp(entry->d_name, "..")) continue;
    if (!entry->d_name[0] || strspn(entry->d_name, "0123456789") != strlen(entry->d_name)) goto done;
    errno = 0;
    char *tail;
    long value = strtol(entry->d_name, &tail, 10);
    if (errno || *tail || value < 0 || value > INT_MAX || s->count == 64) goto done;
    s->fd[s->count++] = (int)value;
  }
  if (errno) goto done;
  for (int i = 0; i < s->count; i++) {
    for (int j = i + 1; j < s->count; j++) {
      if (s->fd[j] < s->fd[i]) { int tmp = s->fd[i]; s->fd[i] = s->fd[j]; s->fd[j] = tmp; }
    }
  }
  for (int i = 0; i < s->count; i++) {
    if (i && s->fd[i] == s->fd[i-1]) goto done;
    if (publish) {
      char name[32];
      struct stat st;
      snprintf(name, sizeof(name), "%d", s->fd[i]);
      /* Re-witness the sorted directory entry, never open/read/hash its target. */
      if (fstatat(dirfd(dir), name, &st, AT_SYMLINK_NOFOLLOW) || !S_ISLNK(st.st_mode)) goto done;
      if (out("FD", ",1,\"PRE_EXEC_INVENTORY\",1,0,%d,null", s->fd[i])) goto done;
      s->fd_seq[i] = sequence;
      s->fd_time[i] = previous_ns;
    }
  }
  result = 0;
done:
  if (closedir(dir)) result = -1;
  return result;
}

static int context(pid_t child, struct snapshot *s)
{
  char path[80], line[256];
  snprintf(path, sizeof(path), "/proc/%d/task", child);
  DIR *dir = opendir(path);
  if (!dir) return -1;
  s->threads = 0;
  struct dirent *entry;
  errno = 0;
  while ((entry = readdir(dir))) {
    if (!strcmp(entry->d_name, ".") || !strcmp(entry->d_name, "..")) continue;
    if (++s->threads > 64) { closedir(dir); return -1; }
  }
  int error = errno;
  if (closedir(dir) || error) return -1;
  snprintf(path, sizeof(path), "/proc/%d/status", child);
  FILE *f = fopen(path, "re");
  if (!f) return -1;
  unsigned a, b, c, d;
  int found = 0;
  while (fgets(line, sizeof(line), f)) {
    if (sscanf(line, "Uid:\t%u\t%u\t%u\t%u", &a, &b, &c, &d) == 4) {
      if (a != b || b != c || c != d) { fclose(f); return -1; }
      s->uid = a; found++;
    }
    if (sscanf(line, "Gid:\t%u\t%u\t%u\t%u", &a, &b, &c, &d) == 4) {
      if (a != b || b != c || c != d) { fclose(f); return -1; }
      s->gid = a; found++;
    }
    if (sscanf(line, "NoNewPrivs:\t%d", &s->nnp) == 1) found++;
  }
  error = ferror(f);
  return fclose(f) || error || found != 3 || s->threads != 1 ? -1 : 0;
}

static int stopped(pid_t *child)
{
  int status;
  pid_t got;
  do { got = waitpid(*child, &status, __WALL); } while (got < 0 && errno == EINTR);
  if (got < 0) { if (errno == ECHILD) *child = -1; return -1; }
  if (WIFEXITED(status) || WIFSIGNALED(status)) { *child = -1; return -1; }
  return WIFSTOPPED(status) && WSTOPSIG(status) == SIGSTOP ? 0 : -1;
}

static int kill_reap(pid_t *child)
{
  int failed = kill(*child, SIGKILL), status;
  pid_t got;
  do { got = waitpid(*child, &status, __WALL); } while (got < 0 && errno == EINTR);
  if (got == *child && (WIFEXITED(status) || WIFSIGNALED(status))) {
    *child = -1;
    return !failed && WIFSIGNALED(status) && WTERMSIG(status) == SIGKILL ? 0 : -1;
  }
  if (got < 0 && errno == ECHILD) *child = -1;
  return -1;
}

static void bootstrap(pid_t parent, int primary, const struct profile *p)
{
  if (prctl(PR_SET_PDEATHSIG, SIGKILL) || getppid() != parent ||
      syscall(SYS_close_range, 0, UINT_MAX, 0) || ptrace(PTRACE_TRACEME, 0, 0, 0)) _exit(2);
  if (raise(SIGSTOP)) _exit(2);
  if (p->count) {
    char path[80];
    snprintf(path, sizeof(path), "/proc/%d/fd/%d", parent, primary);
    int held = open(path, O_RDONLY | O_CLOEXEC);
    if (held < 0) _exit(2);
    int retain = 0;
    for (int i = 0; i < p->count; i++) {
      if (held == p->installed[i]) retain = 1;
      else if (dup2(held, p->installed[i]) != p->installed[i]) _exit(2);
    }
    if (!retain && close(held)) _exit(2);
  }
  if (setgroups(0, NULL) || setgid(65534) || setuid(65534) ||
      prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) || raise(SIGSTOP)) _exit(2);
  _exit(2); /* Parent must never resume this final point, even for NO_DENIAL. */
}

static int member(const int *values, int count, int fd)
{
  for (int i = 0; i < count; i++) if (values[i] == fd) return 1;
  return 0;
}

static int decision(const struct snapshot *s, const int *expected, int count)
{
  int extra[64], extras = 0, missing = 0;
  for (int i = 0; i < count; i++) if (!member(s->fd, s->count, expected[i])) missing++;
  for (int i = 0; i < s->count; i++) {
    if (!member(expected, count, s->fd[i])) extra[extras++] = i;
  }
  if (!missing && extras) {
    for (int i = 0; i < extras; i++) {
      int at = extra[i];
      if (out("CAUSE", ",1,%d,%" PRIu64, s->fd[at], s->fd_seq[at])) return -1;
    }
    return out("DENY", ",1,\"PRE_EXEC_INVENTORY\",1,0,1,\"UNEXPECTED_FD\",null,%d", extras);
  }
  const char *result = missing ? (extras ? "UNSUPPORTED_MIXED" : "UNSUPPORTED_MISSING") : "NO_DENIAL";
  return out("RESULT", ",1,\"PRE_EXEC_INVENTORY\",1,0,1,\"%s\"", result);
}

static int collect(const struct profile *p)
{
  unsigned char random[16];
  char capture[33];
  if (guest_guard() || getrandom(random, sizeof(random), 0) != (ssize_t)sizeof(random) ||
      setvbuf(stdout, NULL, _IOLBF, 0)) return 2;
  for (size_t i = 0; i < sizeof(random); i++) snprintf(capture + i*2, 3, "%02x", random[i]);
  if (out("BEGIN", ",\"guest-data-fd-denial-observed-v2\",\"%s\",\"%s\",\"%s\","
      "\"GUEST_MONOTONIC_NS\",\"OBSERVED_UNTRUSTED\",\"%s\"", capture, SOURCE_REVISION,
      SOURCE_MANIFEST_DIGEST, p->label) || out("POLICY", ",1,%d,1", p->subject) ||
      out("EXPECT", ",1,%d", p->subject)) return 2;
  int rw = -1, ro = -1, result = 2;
  pid_t child = -1;
  rw = memfd_create("fixed-denial-data", MFD_CLOEXEC | MFD_ALLOW_SEALING | 8);
  const char bytes[] = "fixed DATA bytes\n";
  if (rw < 0 || write(rw, bytes, sizeof(bytes)-1) != (ssize_t)(sizeof(bytes)-1) ||
      fcntl(rw, F_ADD_SEALS, 47)) goto done;
  char path[80];
  snprintf(path, sizeof(path), "/proc/self/fd/%d", rw);
  ro = open(path, O_RDONLY | O_CLOEXEC);
  if (ro < 0) goto done;
  pid_t parent = getpid();
  child = fork();
  if (child < 0) goto done;
  if (!child) bootstrap(parent, ro, p);
  if (stopped(&child) || ptrace(PTRACE_SETOPTIONS, child, 0, PTRACE_O_EXITKILL) ||
      out("BIRTH", ",1,0")) goto done;
  struct snapshot initial = {0}, s = {0};
  if (inventory(child, &initial, 0) || context(child, &initial) || initial.count ||
      initial.uid || initial.gid || initial.nnp) goto done;
  if (ptrace(PTRACE_CONT, child, 0, 0) || stopped(&child)) goto done;
  if (inventory(child, &s, 1) || context(child, &s) || s.uid != 65534 || s.gid != 65534 ||
      s.nnp != 1) goto done;
  if (out("SNAP", ",1,\"PRE_EXEC_INVENTORY\",1,0,1,%d,%d,%u,%u,%d,null,null",
          s.count, s.threads, s.uid, s.gid, s.nnp) || decision(&s, &p->subject, 1)) goto done;
  if (kill_reap(&child) || out("REAP", ",1,0,\"SIGNALLED\",9")) goto done;
  if (close(ro)) { ro = -1; goto done; }
  ro = -1;
  if (close(rw)) { rw = -1; goto done; }
  rw = -1;
  if (out("END", ",1,0,null") || fflush(stdout) || ferror(stdout)) goto done;
  result = 0;
done:
  if (child > 0) (void)kill_reap(&child); /* Error cleanup; never resume or forge END. */
  if (ro >= 0 && close(ro)) result = 2;
  if (rw >= 0 && close(rw)) result = 2;
  return result;
}

int main(int argc, char **argv)
{
  if (argc != 3 || strcmp(argv[1], "--probe")) return 2;
  for (size_t i = 0; i < sizeof(profiles)/sizeof(profiles[0]); i++) {
    if (!strcmp(argv[2], profiles[i].label)) return collect(&profiles[i]);
  }
  return 2;
}
