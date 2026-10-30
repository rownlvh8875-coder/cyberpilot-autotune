#ifndef HARMLESS_COMMON_H
#define HARMLESS_COMMON_H
#include <stdint.h>
#include <sys/types.h>

struct guard_config {
  uint64_t payload_cgid, broker_cgid, deny_ino;
  uint32_t deny_major, deny_minor;
};
struct guard_event {
  uint64_t sequence, mono_ns, cgroup_id, pid_tgid, inode;
  uint32_t mode, denied;
};
struct guard_counts { uint64_t sequence, dropped, denials; };
struct broker_result {
  int lookup_calls, reply_errno, addfd_result, object_matches, read_only;
  int copy_ready, mutation_done, copied_path_used;
  uint64_t request_id;
  uint64_t expected_ino, expected_dev;
};
struct child_result { int result_fd, error, read_matches, second_error; };

int run_fixture(const char *fixture_id, int report_fd);
int broker_readonly_main(int listener_fd, int approved_root_fd, int report_fd);
int install_payload_filter(void);
void broker_bind(pid_t pid, const char *fixture_id, struct broker_result *result);
#endif
