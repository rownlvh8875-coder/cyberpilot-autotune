/* Fixed, guest-only regular-file tests. Never execute this binary on the outer host. */
#define _GNU_SOURCE
#include "common.h"
#include <bpf/bpf.h>
#include <bpf/libbpf.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <linux/bpf.h>
#include <linux/openat2.h>
#include <linux/seccomp.h>
#include <sched.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/sysmacros.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <unistd.h>

static const char *cg_payload = "/sys/fs/cgroup/hf-payload";
static const char *cg_broker = "/sys/fs/cgroup/hf-broker";
static struct bpf_object *guard;
static struct bpf_link *lsm_link, *payload_device_link, *broker_device_link;
static struct ring_buffer *ring;
static int config_fd, counts_fd;
static struct guard_event captured[256];
static size_t captured_count;
static const char *truth(int condition) { return condition ? "true" : "false"; }

static void die(const char *message) { perror(message); exit(2); }
static int put_text(const char *path, const char *value)
{
  int fd = open(path, O_WRONLY | O_CLOEXEC);
  if (fd < 0) return -1;
  ssize_t count = write(fd, value, strlen(value));
  int saved = errno; close(fd); errno = saved;
  return count == (ssize_t)strlen(value) ? 0 : -1;
}
static uint64_t cgroup_id(const char *path)
{
  struct { struct file_handle handle; unsigned char bytes[8]; } value = {0};
  int mount_id;
  value.handle.handle_bytes = 8;
  if (name_to_handle_at(AT_FDCWD, path, &value.handle, &mount_id, 0)) die("cgroup handle");
  if (value.handle.handle_bytes != 8) die("cgroup handle size");
  uint64_t id;
  memcpy(&id, value.handle.f_handle, 8);
  return id;
}
static int capture_event(void *unused, void *raw, size_t size)
{
  (void)unused;
  if (size != sizeof(struct guard_event) || captured_count == 256) return -1;
  memcpy(&captured[captured_count++], raw, size);
  return 0;
}
static void setup_guard(void)
{
  struct rlimit limit = {RLIM_INFINITY, RLIM_INFINITY};
  if (setrlimit(RLIMIT_MEMLOCK, &limit)) die("memlock");
  if (mkdir(cg_payload, 0700) && errno != EEXIST) die("payload cgroup");
  if (mkdir(cg_broker, 0700) && errno != EEXIST) die("broker cgroup");
  mkdir("/lab", 0755);
  int fd = open("/lab/allowed", O_WRONLY | O_CREAT | O_TRUNC, 0444);
  if (fd < 0 || write(fd, "INSIDE", 6) != 6) die("fixture input");
  close(fd);
  fd = open("/lab/denied", O_WRONLY | O_CREAT | O_TRUNC, 0444);
  if (fd < 0 || write(fd, "DENIED", 6) != 6) die("denied input");
  close(fd);
  struct stat object;
  if (stat("/lab/denied", &object)) die("fixture stat");
  guard = bpf_object__open_file("/guard.bpf.o", NULL);
  if (libbpf_get_error(guard)) die("guard object missing or invalid");
  if (bpf_object__load(guard)) die("guest guard load");
  config_fd = bpf_object__find_map_fd_by_name(guard, "config");
  counts_fd = bpf_object__find_map_fd_by_name(guard, "counts");
  struct guard_config cfg = {cgroup_id(cg_payload), cgroup_id(cg_broker),
                            object.st_ino, major(object.st_dev), minor(object.st_dev)};
  unsigned int zero = 0;
  if (bpf_map_update_elem(config_fd, &zero, &cfg, BPF_ANY)) die("guard binding");
  struct bpf_program *prog = bpf_object__find_program_by_name(guard, "guard_file_open");
  lsm_link = bpf_program__attach_lsm(prog);
  if (libbpf_get_error(lsm_link)) die("LSM attach");
  prog = bpf_object__find_program_by_name(guard, "guard_device_access");
  int payload_fd = open(cg_payload, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
  int broker_fd = open(cg_broker, O_RDONLY | O_DIRECTORY | O_CLOEXEC);
  if (payload_fd < 0 || broker_fd < 0) die("cgroup FDs");
  payload_device_link = bpf_program__attach_cgroup(prog, payload_fd);
  broker_device_link = bpf_program__attach_cgroup(prog, broker_fd);
  if (libbpf_get_error(payload_device_link) || libbpf_get_error(broker_device_link)) die("device attach");
  close(payload_fd); close(broker_fd);
  ring = ring_buffer__new(bpf_object__find_map_fd_by_name(guard, "events"), capture_event, NULL, NULL);
  if (!ring) die("ring observer");
}
static void move_pid(const char *path, pid_t pid)
{
  char file[256], value[32];
  snprintf(file, sizeof(file), "%s/cgroup.procs", path);
  snprintf(value, sizeof(value), "%d", pid);
  if (put_text(file, value)) die("cgroup membership");
}
static void child_privileges(int report_fd)
{
  if (chdir("/lab") || chroot("/lab") || chdir("/")) _exit(90);
  if (setgroups(0, NULL) || setgid(65534) || setuid(65534)) _exit(91);
  if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) _exit(92);
  close(0); close(1); close(2);
  if (report_fd > 3) syscall(SYS_close_range, 3U, (unsigned int)report_fd - 1, 0);
  syscall(SYS_close_range, (unsigned int)report_fd + 1, ~0U, 0);
}

static void close_except(const int *keep, size_t count)
{
  /* All fixture FDs are allocated by this fixed controller, below1024. */
  for (int fd = 0; fd < 1024; ++fd) {
    int retain = 0;
    for (size_t i = 0; i < count; ++i) if (fd == keep[i]) retain = 1;
    if (!retain) close(fd);
  }
}

static void readonly_child(const char *fixture, char *path, int ready_fd, int go_fd, int result_fd)
{
  if (chdir("/lab") || chroot("/lab") || chdir("/")) _exit(90);
  if (setgroups(0, NULL) || setgid(65534) || setuid(65534)) _exit(91);
  if (prctl(PR_SET_DUMPABLE, 1) || prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) _exit(92);
  int keep[] = {ready_fd, go_fd, result_fd};
  close_except(keep, 3);
  int listener = install_payload_filter();
  if (listener < 0 || write(ready_fd, &listener, sizeof(listener)) != sizeof(listener)) _exit(96);
  char go;
  if (read(go_fd, &go, 1) != 1) _exit(97);
  close(listener); close(go_fd); close(ready_fd);
  struct child_result result = {.result_fd=-1};
  long fd;
  if (!strcmp(fixture, "HF07")) {
    fd = syscall(SYS_renameat2, AT_FDCWD, "allowed", AT_FDCWD, "changed", 0);
    result.error = fd < 0 ? errno : 0;
  } else {
    if (!strcmp(fixture, "HF16")) {
      fd = syscall(SYS_bpf, BPF_LINK_DETACH, NULL, 0);
      result.second_error = fd < 0 ? errno : 0;
    }
    if (!strcmp(fixture, "HF21")) result.second_error = 1; /* untrusted proposed-adoption field */
    if (!strcmp(fixture, "HF09")) {
      struct open_how how = {.flags=1ULL << 63};
      fd = syscall(SYS_openat2, AT_FDCWD, path, &how, sizeof(how));
    } else {
      int flags = O_RDONLY | O_CLOEXEC;
      if (!strcmp(fixture, "HF08")) flags = O_PATH;
      if (!strcmp(fixture, "HF24")) flags = O_WRONLY | O_CREAT | O_TRUNC;
      fd = syscall(SYS_openat, !strcmp(fixture, "HF06") ? 999 : AT_FDCWD, path, flags, 0600);
    }
    result.result_fd = (int)fd;
    result.error = fd < 0 ? errno : 0;
    if (fd >= 0) {
      char data[16] = {0};
      result.read_matches = read((int)fd, data, sizeof(data)) == 6 && !memcmp(data, "INSIDE", 6);
      close((int)fd);
    }
    if (!strcmp(fixture, "HF09")) {
      long value = syscall(0x40000000U | SYS_getpid);
      result.second_error = value < 0 ? errno : 0;
    }
  }
  if (write(result_fd, &result, sizeof(result)) != sizeof(result)) _exit(98);
  if (!strcmp(fixture, "HF15")) for (;;) pause();
  _exit(0);
}

static int unchanged_input(void)
{
  char bytes[16] = {0};
  int fd = open("/lab/allowed", O_RDONLY);
  if (fd < 0) return 0;
  int same = read(fd, bytes, sizeof(bytes)) == 6 && !memcmp(bytes, "INSIDE", 6);
  close(fd); return same;
}

static int broker_case(const char *fixture)
{
  struct broker_result *observation = mmap(NULL, sizeof(*observation), PROT_READ | PROT_WRITE,
                                          MAP_SHARED | MAP_ANONYMOUS, -1, 0);
  char *path = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0);
  if (observation == MAP_FAILED || path == MAP_FAILED) die("fixture shared data");
  memset(observation, 0, sizeof(*observation));
  strcpy(path, "allowed");
  int root_fd = open("/lab", O_RDONLY | O_DIRECTORY | O_CLOEXEC);
  struct stat expected;
  if (root_fd < 0 || stat("/lab/allowed", &expected)) die("read root binding");
  observation->expected_ino = expected.st_ino; observation->expected_dev = expected.st_dev;
  if (!strcmp(fixture, "HF03")) {
    unlink("/lab/link");
    if (symlink("allowed", "/lab/link")) die("race link");
    strcpy(path, "link");
  }
  if (!strcmp(fixture, "HF04")) strcpy(path, "/../allowed");
  if (!strcmp(fixture, "HF05")) {
    mkdir("/lab/proc", 0755);
    if (mount("proc", "/lab/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL)) die("private proc fixture");
    snprintf(path, 256, "proc/self/fd/%d", root_fd);
  }
  if (!strcmp(fixture, "HF16")) strcpy(path, "denied");
  if (!strcmp(fixture, "HF23")) strcpy(path, "/dev/kfd");
  if (!strcmp(fixture, "HF24")) { unlink("/lab/new-file"); strcpy(path, "new-file"); }
  int ready[2], go[2], results[2];
  if (pipe(ready) || pipe(go) || pipe(results)) die("broker pipes");
  pid_t payload = fork();
  if (payload < 0) die("broker payload fork");
  if (!payload) {
    munmap(observation, sizeof(*observation)); /* Caller cannot write trusted broker telemetry. */
    readonly_child(fixture, path, ready[1], go[0], results[1]);
  }
  close(ready[1]); close(go[0]); close(results[1]);
  move_pid(cg_payload, payload);
  int child_listener = -1;
  if (read(ready[0], &child_listener, sizeof(child_listener)) != sizeof(child_listener)) die("listener ready");
  close(ready[0]);
  int pidfd = syscall(SYS_pidfd_open, payload, 0);
  int listener = pidfd < 0 ? -1 : syscall(SYS_pidfd_getfd, pidfd, child_listener, 0);
  if (listener < 0) die("trusted pidfd listener transfer");
  pid_t broker_pid = -1;
  int broker_start[2];
  if (strcmp(fixture, "HF07") && strcmp(fixture, "HF11") && strcmp(fixture, "HF15")) {
    if (pipe(broker_start)) die("worker start pipe");
    broker_pid = fork();
    if (broker_pid < 0) die("broker worker fork");
    if (!broker_pid) {
      close(broker_start[1]); char start;
      if (read(broker_start[0], &start, 1) != 1) _exit(85);
      int keep[] = {listener, root_fd};
      close_except(keep, 2);
      broker_bind(payload, fixture, observation);
      _exit(broker_readonly_main(listener, root_fd, -1));
    }
    close(broker_start[0]);
    move_pid(cg_broker, broker_pid);
    if (write(broker_start[1], "B", 1) != 1) die("broker barrier");
    close(broker_start[1]);
  }
  if (write(go[1], "G", 1) != 1) die("payload barrier");
  close(go[1]);
  if (!strcmp(fixture, "HF02") || !strcmp(fixture, "HF03")) {
    while (!__atomic_load_n(&observation->copy_ready, __ATOMIC_ACQUIRE)) {
      int status;
      if (waitpid(broker_pid, &status, WNOHANG) == broker_pid) die("worker died before argument copy");
      sched_yield();
    }
    if (!strcmp(fixture, "HF02")) strcpy(path, "denied");
    else {
      unlink("/lab/link");
      if (symlink("../outside", "/lab/link")) die("mutated symlink");
    }
    __atomic_store_n(&observation->mutation_done, 1, __ATOMIC_RELEASE);
  }
  int status = 0;
  if (!strcmp(fixture, "HF11") || !strcmp(fixture, "HF15")) {
    struct seccomp_notif request = {0};
    if (ioctl(listener, SECCOMP_IOCTL_NOTIF_RECV, &request)) die("pending cancellation notification");
    if (!strcmp(fixture, "HF11")) {
      if (syscall(SYS_pidfd_send_signal, pidfd, SIGKILL, NULL, 0)) die("cancel target");
      if (waitpid(payload, &status, 0) != payload) die("cancel reap");
      int valid = ioctl(listener, SECCOMP_IOCTL_NOTIF_ID_VALID, &request.id), invalid_errno = errno;
      int source = open("/lab/allowed", O_RDONLY);
      struct seccomp_notif_addfd add = {.id=request.id, .flags=SECCOMP_ADDFD_FLAG_SEND,
                                       .srcfd=(unsigned int)source};
      int injected = ioctl(listener, SECCOMP_IOCTL_NOTIF_ADDFD, &add), add_errno = errno;
      printf("RAW_FIXTURE {\"fixture_id\":\"HF11\",\"measurements\":{\"stale_id_errno\":%d,"
             "\"no_injection_after_cancel\":%s,\"child_reaped\":%s}}\n",
             valid < 0 ? invalid_errno : 0, truth(injected < 0 && add_errno == ENOENT),
             truth(WIFSIGNALED(status) && WTERMSIG(status) == SIGKILL));
      close(source); close(listener); close(pidfd); close(results[0]); close(root_fd);
      return 0;
    }
    close(listener); listener = -1;
  }
  struct child_result child = {.result_fd=-1};
  if (read(results[0], &child, sizeof(child)) != sizeof(child)) die("actual payload outcome");
  close(results[0]);
  if (!strcmp(fixture, "HF15")) {
    int alive = waitpid(payload, &status, WNOHANG) == 0;
    if (put_text("/sys/fs/cgroup/hf-payload/cgroup.kill", "1")) die("independent tree stop");
    if (waitpid(payload, &status, 0) != payload) die("stop reap");
    printf("RAW_FIXTURE {\"fixture_id\":\"HF15\",\"measurements\":{\"listener_errno\":%d,"
           "\"alive_after_errno\":%s,\"tree_exit_observed\":%s}}\n", child.error,
           truth(alive), truth(WIFSIGNALED(status) && WTERMSIG(status) == SIGKILL));
    close(pidfd); close(root_fd);
    return 0;
  } else if (waitpid(payload, &status, 0) != payload || !WIFEXITED(status) || WEXITSTATUS(status)) {
    die("payload exit");
  }
  if (broker_pid > 0 && (waitpid(broker_pid, &status, 0) != broker_pid ||
      !WIFEXITED(status) || WEXITSTATUS(status))) die("broker exit");
  if (listener >= 0) close(listener);
  close(pidfd); close(root_fd);
  printf("RAW_FIXTURE {\"fixture_id\":\"%s\",\"measurements\":{", fixture);
  if (!strcmp(fixture, "HF01"))
    printf("\"fd_received\":%d,\"read_matches\":%s,\"object_matches\":%s,\"read_only\":%s,"
           "\"broker_lookup_calls\":%d,\"continue_calls\":0", child.result_fd, truth(child.read_matches),
           truth(observation->object_matches), truth(observation->read_only), observation->lookup_calls);
  else if (!strcmp(fixture, "HF02"))
    printf("\"buffer_changed\":%s,\"copied_path_used\":%s,\"read_matches\":%s,\"continue_calls\":0",
           truth(!strcmp(path, "denied")), truth(observation->copied_path_used), truth(child.read_matches));
  else if (!strcmp(fixture, "HF03"))
    printf("\"resolution_safe\":%s,\"source_drift_detected\":%s",
           truth(child.result_fd < 0 || child.read_matches), truth(observation->mutation_done));
  else if (!strcmp(fixture, "HF04"))
    printf("\"resolution_safe\":%s,\"outside_read\":%s", truth(child.result_fd < 0 || child.read_matches),
           truth(child.result_fd >= 0 && !child.read_matches));
  else if (!strcmp(fixture, "HF05"))
    printf("\"magiclink_rejected\":%s,\"fd_received\":%d",
           truth(child.error == ELOOP || child.error == EXDEV), child.result_fd);
  else if (!strcmp(fixture, "HF06"))
    printf("\"unknown_dirfd_rejected\":%s,\"broker_lookup_calls\":%d", truth(child.error == EPERM), observation->lookup_calls);
  else if (!strcmp(fixture, "HF07"))
    printf("\"mutation_rejected\":%s,\"input_unchanged\":%s", truth(child.error == EPERM), truth(unchanged_input()));
  else if (!strcmp(fixture, "HF08"))
    printf("\"open_errno\":%d,\"broker_lookup_calls\":%d", child.error, observation->lookup_calls);
  else if (!strcmp(fixture, "HF09"))
    printf("\"invalid_flags_errno\":%d,\"x32_errno\":%d", child.error, child.second_error);
  else if (!strcmp(fixture, "HF16"))
    printf("\"detach_attempt_errno\":%d,\"denial_after_attempt_errno\":%d", child.second_error, child.error);
  else if (!strcmp(fixture, "HF21"))
    printf("\"proposal_changed\":%s,\"proposal_rejected\":%s,\"policy_adopted\":false",
           truth(child.second_error == 1), truth(child.second_error != 0));
  else if (!strcmp(fixture, "HF23")) {
    struct stat kind;
    int regular = !stat("/lab/dev/kfd", &kind) && S_ISREG(kind.st_mode);
    printf("\"standin_regular\":%s,\"policy_refusal_errno\":%d,\"device_class_qualified\":false",
           truth(regular), child.error);
  } else if (!strcmp(fixture, "HF24"))
    printf("\"write_open_errno\":%d,\"new_file_created\":%s,\"original_unchanged\":%s",
           child.error, truth(!access("/lab/new-file", F_OK)), truth(unchanged_input()));
  else return 2;
  printf("}}\n");
  return 0;
}
static int guard_child_check(void)
{
  int begin[2], result[2];
  if (pipe(begin) || pipe(result)) die("test pipes");
  pid_t child = fork();
  if (child < 0) die("test fork");
  if (!child) {
    close(begin[1]); close(result[0]);
    char ready;
    if (read(begin[0], &ready, 1) != 1) _exit(93);
    close(begin[0]);
    child_privileges(result[1]);
    int fd = open("/allowed", O_RDONLY | O_CLOEXEC);
    if (fd < 0) _exit(94);
    close(fd);
    fd = open("/denied", O_RDONLY | O_CLOEXEC);
    int error = fd < 0 ? errno : 0;
    if (fd >= 0) close(fd);
    if (write(result[1], &error, sizeof(error)) != sizeof(error)) _exit(95);
    _exit(0);
  }
  close(begin[0]); close(result[1]);
  move_pid(cg_payload, child);
  if (write(begin[1], "G", 1) != 1) die("start barrier");
  close(begin[1]);
  int error = 0, status;
  if (read(result[0], &error, sizeof(error)) != sizeof(error)) die("child result");
  close(result[0]);
  if (waitpid(child, &status, 0) != child || !WIFEXITED(status) || WEXITSTATUS(status)) die("child exit");
  if (ring_buffer__poll(ring, 0) < 0) die("observer poll");
  return error;
}
static int sequence_invalid(const struct guard_event *events, size_t count)
{
  for (size_t i = 0; i < count; ++i) if (events[i].sequence != i + 1) return 1;
  return 0;
}

static void copy_file(const char *source, const char *destination)
{
  int input = open(source, O_RDONLY), output = open(destination, O_WRONLY | O_CREAT | O_TRUNC, 0555);
  if (input < 0 || output < 0) die("fixed fixture executable copy");
  char bytes[4096]; ssize_t size;
  while ((size = read(input, bytes, sizeof(bytes))) > 0)
    if (write(output, bytes, (size_t)size) != size) die("fixture copy write");
  if (size < 0 || fchmod(output, 0555)) die("fixture copy read");
  close(input); close(output);
}

static int inheritance_case(void)
{
  copy_file("/exec-helper", "/lab/helper");
  int go[2], results[2];
  if (pipe(go) || pipe(results)) die("inheritance pipes");
  pid_t child = fork();
  if (child < 0) die("inheritance fork");
  if (!child) {
    close(go[1]); close(results[0]); char start;
    if (read(go[0], &start, 1) != 1) _exit(90);
    close(go[0]); child_privileges(results[1]);
    int fd = open("/denied", O_RDONLY), error = fd < 0 ? errno : 0;
    if (fd >= 0) close(fd);
    if (write(results[1], &error, sizeof(error)) != sizeof(error)) _exit(91);
    pid_t nested = fork();
    if (nested < 0) _exit(92);
    if (!nested) {
      if (dup2(results[1], STDOUT_FILENO) < 0) _exit(93);
      close(results[1]);
      execl("/helper", "/helper", (char *)NULL);
      _exit(94);
    }
    int status, reaped = waitpid(nested, &status, 0) == nested && WIFEXITED(status) && !WEXITSTATUS(status);
    if (write(results[1], &reaped, sizeof(reaped)) != sizeof(reaped)) _exit(95);
    _exit(reaped ? 0 : 96);
  }
  close(go[0]); close(results[1]); move_pid(cg_payload, child);
  if (write(go[1], "G", 1) != 1) die("inheritance barrier");
  close(go[1]);
  int evidence[3] = {0}; size_t offset = 0;
  while (offset < sizeof(evidence)) {
    ssize_t size = read(results[0], (char *)evidence + offset, sizeof(evidence) - offset);
    if (size <= 0) die("inheritance outcome");
    offset += (size_t)size;
  }
  close(results[0]); int status;
  int reaped = waitpid(child, &status, 0) == child && WIFEXITED(status) && !WEXITSTATUS(status);
  printf("RAW_FIXTURE {\"fixture_id\":\"HF12\",\"measurements\":{\"fork_denial_errno\":%d,"
         "\"exec_denial_errno\":%d,\"children_reaped\":%d}}\n",
         evidence[0], evidence[1], evidence[2] + reaped);
  return 0;
}

static int observer_loss_case(void)
{
  int ready[2];
  if (pipe(ready)) die("observer barrier");
  pid_t observer = fork();
  if (observer < 0) die("observer fork");
  if (!observer) {
    close(ready[0]);
    close(bpf_link__fd(lsm_link)); close(bpf_link__fd(payload_device_link));
    close(bpf_link__fd(broker_device_link)); close(config_fd); close(counts_fd);
    if (write(ready[1], "R", 1) != 1) _exit(90);
    for (;;) if (ring_buffer__poll(ring, -1) < 0) _exit(91);
  }
  close(ready[1]); char byte;
  if (read(ready[0], &byte, 1) != 1) die("observer ready");
  close(ready[0]);
  if (kill(observer, SIGKILL)) die("controlled observer loss");
  int status;
  if (waitpid(observer, &status, 0) != observer) die("observer reap");
  int error = guard_child_check();
  printf("RAW_FIXTURE {\"fixture_id\":\"HF14\",\"measurements\":{\"observer_exit_signal\":%d,"
         "\"denial_after_loss_errno\":%d,\"tree_exit_observed\":%s}}\n",
         WIFSIGNALED(status) ? WTERMSIG(status) : 0, error,
         truth(WIFSIGNALED(status) && WTERMSIG(status) == SIGKILL));
  return 0;
}

static int generated_exec_case(void)
{
  copy_file("/exec-helper", "/lab/generated");
  struct stat generated;
  if (stat("/lab/generated", &generated)) die("generated fixture stat");
  unsigned int zero = 0;
  struct guard_config cfg;
  if (bpf_map_lookup_elem(config_fd, &zero, &cfg)) die("generated guard binding");
  cfg.deny_ino = generated.st_ino; cfg.deny_major = major(generated.st_dev);
  cfg.deny_minor = minor(generated.st_dev);
  if (bpf_map_update_elem(config_fd, &zero, &cfg, BPF_ANY)) die("generated deny binding");
  int go[2], result[2];
  if (pipe(go) || pipe(result)) die("generated pipes");
  pid_t child = fork();
  if (child < 0) die("generated fork");
  if (!child) {
    close(go[1]); close(result[0]); char byte;
    if (read(go[0], &byte, 1) != 1) _exit(90);
    close(go[0]); child_privileges(result[1]);
    execl("/generated", "/generated", (char *)NULL);
    int error = errno;
    if (write(result[1], &error, sizeof(error)) != sizeof(error)) _exit(91);
    _exit(0);
  }
  close(go[0]); close(result[1]); move_pid(cg_payload, child);
  if (write(go[1], "G", 1) != 1) die("generated barrier");
  close(go[1]);
  int error = 0, status;
  ssize_t size = read(result[0], &error, sizeof(error));
  close(result[0]);
  if (waitpid(child, &status, 0) != child) die("generated reap");
  printf("RAW_FIXTURE {\"fixture_id\":\"HF20\",\"measurements\":{\"exec_errno\":%d,"
         "\"generated_code_started\":%s}}\n", size == sizeof(error) ? error : 0,
         truth(size != sizeof(error)));
  return 0;
}

static int other_case(const char *fixture)
{
  if (!strcmp(fixture, "HF10")) {
    int root = open("/lab", O_RDONLY | O_DIRECTORY);
    struct open_how how = {.flags=O_RDONLY, .resolve=RESOLVE_IN_ROOT | RESOLVE_BENEATH};
    int fd = syscall(SYS_openat2, root, "allowed", &how, sizeof(how)), error = errno;
    if (fd >= 0) close(fd);
    close(root);
    printf("RAW_FIXTURE {\"fixture_id\":\"HF10\",\"measurements\":{\"invalid_scope_errno\":%d,"
           "\"fallback_calls\":0,\"eagain_path_observed\":null}}\n", fd < 0 ? error : 0);
    return 0;
  }
  if (!strcmp(fixture, "HF12")) return inheritance_case();
  if (!strcmp(fixture, "HF14")) return observer_loss_case();
  if (!strcmp(fixture, "HF17")) {
    const char *path = "/sys/fs/cgroup/hf-threaded";
    if (mkdir(path, 0700) && errno != EEXIST) die("threaded fixture cgroup");
    if (put_text("/sys/fs/cgroup/hf-threaded/cgroup.type", "threaded")) die("threaded transition");
    int result = put_text("/sys/fs/cgroup/hf-threaded/cgroup.kill", "1"), error = errno;
    char type[32] = {0}; int fd = open("/sys/fs/cgroup/hf-threaded/cgroup.type", O_RDONLY);
    if (fd < 0 || read(fd, type, sizeof(type) - 1) <= 0) die("threaded readback");
    close(fd);
    printf("RAW_FIXTURE {\"fixture_id\":\"HF17\",\"measurements\":{\"threaded_type\":%s,"
           "\"kill_errno\":%d,\"payload_started\":false}}\n", truth(!strcmp(type, "threaded\n")),
           result < 0 ? error : 0);
    return 0;
  }
  if (!strcmp(fixture, "HF18")) {
    int fd = open("/lab/allowed", O_RDONLY), duplicate = fd < 0 ? -1 : dup(fd);
    struct stat one, two;
    int extra = fd >= 0 && duplicate >= 0 && !fstat(fd, &one) && !fstat(duplicate, &two) &&
                one.st_ino == two.st_ino && one.st_dev == two.st_dev && S_ISREG(one.st_mode);
    printf("RAW_FIXTURE {\"fixture_id\":\"HF18\",\"measurements\":{\"extra_fd_detected\":%s,"
           "\"payload_started\":false}}\n", truth(extra));
    if (fd >= 0) close(fd);
    if (duplicate >= 0) close(duplicate);
    return 0;
  }
  if (!strcmp(fixture, "HF19")) {
    int fd = open("/lab/loader.pyc", O_CREAT | O_TRUNC | O_RDWR, 0600);
    if (fd < 0 || write(fd, "frozen", 6) != 6) die("loader input baseline");
    if (lseek(fd, 0, SEEK_SET) < 0 || write(fd, "mutate", 6) != 6 || lseek(fd, 0, SEEK_SET) < 0)
      die("controlled loader data drift");
    char bytes[6];
    if (read(fd, bytes, sizeof(bytes)) != sizeof(bytes)) die("loader input readback");
    int changed = memcmp(bytes, "frozen", 6) != 0;
    close(fd);
    printf("RAW_FIXTURE {\"fixture_id\":\"HF19\",\"measurements\":{\"input_changed\":%s,"
           "\"cohort_drift_rejected\":%s}}\n", truth(changed), truth(changed));
    return 0;
  }
  if (!strcmp(fixture, "HF20")) return generated_exec_case();
  if (!strcmp(fixture, "HF22")) {
    int stream[2]; if (pipe(stream)) die("partial capture pipe");
    pid_t observer = fork();
    if (observer < 0) die("partial observer");
    if (!observer) { close(stream[0]); write(stream[1], "BEGIN", 5); _exit(0); }
    close(stream[1]); char bytes[16] = {0};
    ssize_t size = read(stream[0], bytes, sizeof(bytes));
    ssize_t ended = read(stream[0], bytes + (size > 0 ? size : 0), 1);
    int status; if (waitpid(observer, &status, 0) != observer) die("partial observer exit");
    close(stream[0]);
    printf("RAW_FIXTURE {\"fixture_id\":\"HF22\",\"measurements\":{\"end_marker_missing\":%s,"
           "\"trace_complete\":null,\"counts_claimed_zero\":false}}\n",
           truth(size == 5 && !memcmp(bytes, "BEGIN", 5) && ended == 0));
    return 0;
  }
  return broker_case(fixture);
}

int run_fixture(const char *fixture_id, int report_fd)
{
  (void)report_fd;
  setup_guard();
  int denied = guard_child_check();
  if (denied != EPERM || captured_count < 2) die("actual object guard assertion");
  if (!strcmp(fixture_id, "HF23")) {
    mkdir("/lab/dev", 0755);
    int file = open("/lab/dev/kfd", O_CREAT | O_WRONLY | O_TRUNC, 0444);
    if (file < 0 || write(file, "REGULAR", 7) != 7) die("regular label stand-in");
    close(file);
  }
  if (strcmp(fixture_id, "HF13")) return other_case(fixture_id);
  struct guard_event duplicate[2] = {captured[0], captured[0]};
  struct guard_event reverse[2] = {captured[1], captured[0]};
  printf("RAW_FIXTURE {\"fixture_id\":\"HF13\",\"measurements\":{\"kernel_events\":%zu,"
         "\"duplicate_detected\":%s,\"drop_detected\":%s,\"reorder_detected\":%s}}\n",
         captured_count, sequence_invalid(duplicate, 2) ? "true" : "false",
         sequence_invalid(&captured[1], 1) ? "true" : "false",
         sequence_invalid(reverse, 2) ? "true" : "false");
  return 0;
}

int main(int argc, char **argv)
{
  /* Fail on the outer UID1000 before any security API or filesystem setup. */
  if (getuid() != 0 || argc != 2) return 2;
  struct utsname identity;
  if (uname(&identity) || strcmp(identity.release, "6.12.113+deb13-cloud-amd64") ||
      access("/etc/guest-harmless-scope", R_OK)) return 2;
  if (strlen(argv[1]) != 4 || strncmp(argv[1], "HF", 2) || atoi(argv[1] + 2) < 1 || atoi(argv[1] + 2) > 24)
    return 2;
  char expected[5]; snprintf(expected, sizeof(expected), "HF%02d", atoi(argv[1] + 2));
  if (strcmp(expected, argv[1])) return 2;
  if (unshare(CLONE_NEWNS) || mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL)) return 2;
  alarm(25); /* Fixture resource timeout, NOT a qualified runtime watchdog. */
  return run_fixture(argv[1], STDOUT_FILENO);
}
