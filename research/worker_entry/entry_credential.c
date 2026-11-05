/* Reuse unchanged component in a separate TU so ONLY its syscall boundary
 * can be replaced by the no-forward test shim. Native clone/exec stay real. */
#include "../credential_seal/seal.c"
#include "entry_credential.h"
int entry_prebirth(struct ce_attempt *attempt,const struct ce_ids *p) {
  if(!attempt)return CE_REJECTED;
  if(atomic_exchange_explicit(&attempt->consumed,1,memory_order_acq_rel))
    return CE_ALREADY_ATTEMPTED;
  if(!valid_ids(p))return CE_REJECTED;
  struct snapshot s;int r=read_snapshot(&s);
  if(r==-2)return CE_UNKNOWN;
  if(r || !match(&s,p->owner_uid,p->owner_gid,0))return CE_REJECTED;
  struct sock_filter b[CE_FILTER_MAX];
  int n=ce_build_id_filter(p,b,CE_FILTER_MAX);
  if(n<=0)return CE_REJECTED;
  struct sock_fprog f={(unsigned short)n,b};
  if(SC(SYS_seccomp,SECCOMP_SET_MODE_FILTER,0,&f,0,0,0))return CE_UNKNOWN;
  return CE_SEALED_CREDENTIALS_ONLY; /* Prebirth filter only, NOT a seal/authority. */
}
