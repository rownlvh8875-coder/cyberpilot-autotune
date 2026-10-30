/* GPL guest-only guard prototype. Device-class behavior is deliberately UNQUALIFIED. */
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>
#include <bpf/bpf_tracing.h>

struct super_block { unsigned int s_dev; } __attribute__((preserve_access_index));
struct inode {
  unsigned short i_mode;
  unsigned long i_ino;
  struct super_block *i_sb;
} __attribute__((preserve_access_index));
struct file { struct inode *f_inode; } __attribute__((preserve_access_index));
struct guard_config { __u64 payload_cgid, broker_cgid, deny_ino; __u32 deny_major, deny_minor; };
struct guard_event {
  __u64 sequence, mono_ns, cgroup_id, pid_tgid, inode;
  __u32 mode, denied;
};
struct guard_counts { __u64 sequence, dropped, denials; };
struct {
  __uint(type, BPF_MAP_TYPE_ARRAY); __uint(max_entries, 1);
  __type(key, __u32); __type(value, struct guard_config);
} config SEC(".maps");
struct {
  __uint(type, BPF_MAP_TYPE_ARRAY); __uint(max_entries, 1);
  __type(key, __u32); __type(value, struct guard_counts);
} counts SEC(".maps");
struct {
  __uint(type, BPF_MAP_TYPE_RINGBUF); __uint(max_entries, 131072);
} events SEC(".maps");

SEC("lsm/file_open")
long BPF_PROG(guard_file_open, struct file *opened, int previous)
{
  /* Stable6.12.113 requires a proven signed errno range. Register/compiler
   * width alone is insufficient. An invalid nonzero result must still deny. */
  if (previous) {
    if (previous < 0 && previous >= -4095) return (long)previous;
    return -1;
  }
  __u32 key = 0;
  struct guard_config *binding = bpf_map_lookup_elem(&config, &key);
  __u64 group = bpf_get_current_cgroup_id();
  if (!binding || (group != binding->payload_cgid && group != binding->broker_cgid)) return 0;
  struct inode *object = BPF_CORE_READ(opened, f_inode);
  __u64 inode = BPF_CORE_READ(object, i_ino);
  __u32 mode = BPF_CORE_READ(object, i_mode);
  __u32 device = BPF_CORE_READ(object, i_sb, s_dev);
  /* Initial regular-file profile exposes no character/block nodes at all.
   * O_PATH is separately rejected by the broker; this hook cannot mediate it. */
  int reject = (mode & 0170000) == 0020000 || (mode & 0170000) == 0060000;
  if (inode == binding->deny_ino && (device >> 20) == binding->deny_major &&
      (device & ((1U << 20) - 1)) == binding->deny_minor) reject = 1;
  struct guard_counts *state = bpf_map_lookup_elem(&counts, &key);
  if (!state) return -1;
  __u64 sequence = __sync_fetch_and_add(&state->sequence, 1) + 1;
  if (reject) __sync_fetch_and_add(&state->denials, 1);
  struct guard_event *event = bpf_ringbuf_reserve(&events, sizeof(*event), 0);
  if (!event) {
    __sync_fetch_and_add(&state->dropped, 1);
  } else {
    event->sequence = sequence; event->mono_ns = bpf_ktime_get_ns();
    event->cgroup_id = group; event->pid_tgid = bpf_get_current_pid_tgid();
    event->inode = inode; event->mode = mode; event->denied = reject;
    bpf_ringbuf_submit(event, 0);
  }
  volatile long verdict = 0;
  if (reject) verdict = -1;
  return verdict;
}

SEC("cgroup/dev")
int guard_device_access(struct bpf_cgroup_dev_ctx *context)
{
  (void)context;
  /* Attachment only: no device nodes or hardware operations test this branch. */
  return 0;
}
char LICENSE[] SEC("license") = "GPL";
