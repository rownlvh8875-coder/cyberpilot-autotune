#ifndef CE_RESEARCH_SEAL_H
#define CE_RESEARCH_SEAL_H
#include <linux/filter.h>
#include <stdatomic.h>
#include <stddef.h>
#include <stdint.h>

/* Research-only internal component. IDs/results are data, never a live grant.
 * No payload entry, factory registration, main, or public command/FD/PID API. */
#define CE_FILTER_MAX 128
struct ce_ids { uint32_t owner_uid, owner_gid, worker_uid, worker_gid; };
struct ce_attempt { atomic_uint consumed; };
#define CE_ATTEMPT_INIT { ATOMIC_VAR_INIT(0) }
enum ce_result {
  CE_SEALED_CREDENTIALS_ONLY=0, CE_REJECTED=1, CE_UNKNOWN=2, CE_ALREADY_ATTEMPTED=3
};
int ce_build_id_filter(const struct ce_ids *, struct sock_filter *, size_t);
int ce_seal_worker(struct ce_attempt *, const struct ce_ids *);
int ce_seal_owner(struct ce_attempt *, const struct ce_ids *);
#endif
