#ifndef GUEST_COLLECTOR_H
#define GUEST_COLLECTOR_H
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>
#define COLLECTOR_MAX_FDS 4096
struct fd_record { uint64_t fd, flags, dev, inode, mode, mount_id; };
int snapshot_fds(pid_t tid, struct fd_record *records, size_t capacity);
#endif
