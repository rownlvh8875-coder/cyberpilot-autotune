#define _GNU_SOURCE
#include "seal.h"
#include <errno.h>
#include <linux/audit.h>
#include <linux/seccomp.h>
#include <stddef.h>
#include <string.h>
#include <sys/syscall.h>
#if !defined(__x86_64__) || defined(__ILP32__) || __SIZEOF_POINTER__ != 8 || \
    __SIZEOF_LONG__ != 8 || __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "Research credential policy currently supports x86_64 little endian only"
#endif

static int valid_ids(const struct ce_ids *p) {
  return p && p->owner_uid && p->owner_gid && p->worker_uid && p->worker_gid &&
    p->owner_uid != UINT32_MAX && p->owner_gid != UINT32_MAX &&
    p->worker_uid != UINT32_MAX && p->worker_gid != UINT32_MAX &&
    p->owner_uid != p->worker_uid && p->owner_gid != p->worker_gid;
}
static void emit(struct sock_filter *b, size_t *n, unsigned short code,
                 unsigned char jt, unsigned char jf, unsigned int k) {
  b[(*n)++] = (struct sock_filter){code,jt,jf,k};
}
static void exact_arg(struct sock_filter *b,size_t *n,unsigned i,uint32_t want) {
  emit(b,n,BPF_LD|BPF_W|BPF_ABS,0,0,(unsigned)offsetof(struct seccomp_data,args)+i*8+4);
  emit(b,n,BPF_JMP|BPF_JEQ|BPF_K,1,0,0);
  emit(b,n,BPF_RET|BPF_K,0,0,SECCOMP_RET_ERRNO|EPERM);
  emit(b,n,BPF_LD|BPF_W|BPF_ABS,0,0,(unsigned)offsetof(struct seccomp_data,args)+i*8);
  emit(b,n,BPF_JMP|BPF_JEQ|BPF_K,1,0,want);
  emit(b,n,BPF_RET|BPF_K,0,0,SECCOMP_RET_ERRNO|EPERM);
}
int ce_build_id_filter(const struct ce_ids *p,struct sock_filter *out,size_t cap) {
  if(!valid_ids(p) || !out)return -1;
  struct sock_filter b[CE_FILTER_MAX];size_t n=0;
  emit(b,&n,BPF_LD|BPF_W|BPF_ABS,0,0,offsetof(struct seccomp_data,arch));
  emit(b,&n,BPF_JMP|BPF_JEQ|BPF_K,1,0,AUDIT_ARCH_X86_64);
  emit(b,&n,BPF_RET|BPF_K,0,0,SECCOMP_RET_KILL_PROCESS);
  emit(b,&n,BPF_LD|BPF_W|BPF_ABS,0,0,offsetof(struct seccomp_data,nr));
  emit(b,&n,BPF_JMP|BPF_JGE|BPF_K,0,1,0x40000000U);
  emit(b,&n,BPF_RET|BPF_K,0,0,SECCOMP_RET_KILL_PROCESS);
  const unsigned denied[]={SYS_setuid,SYS_setreuid,SYS_setfsuid,
                           SYS_setgid,SYS_setregid,SYS_setfsgid};
  for(size_t i=0;i<sizeof denied/sizeof denied[0];++i) {
    emit(b,&n,BPF_JMP|BPF_JEQ|BPF_K,0,1,denied[i]);
    emit(b,&n,BPF_RET|BPF_K,0,0,SECCOMP_RET_ERRNO|EPERM);
  }
  emit(b,&n,BPF_JMP|BPF_JEQ|BPF_K,0,19,SYS_setresuid);
  for(unsigned i=0;i<3;++i)exact_arg(b,&n,i,p->worker_uid);
  emit(b,&n,BPF_RET|BPF_K,0,0,SECCOMP_RET_ALLOW);
  emit(b,&n,BPF_JMP|BPF_JEQ|BPF_K,0,19,SYS_setresgid);
  for(unsigned i=0;i<3;++i)exact_arg(b,&n,i,p->worker_gid);
  emit(b,&n,BPF_RET|BPF_K,0,0,SECCOMP_RET_ALLOW);
  emit(b,&n,BPF_JMP|BPF_JEQ|BPF_K,0,13,SYS_setgroups);
  exact_arg(b,&n,0,0);exact_arg(b,&n,1,0);
  emit(b,&n,BPF_RET|BPF_K,0,0,SECCOMP_RET_ALLOW);
  emit(b,&n,BPF_RET|BPF_K,0,0,SECCOMP_RET_ALLOW);
  if(cap<n)return -1;
  memcpy(out,b,n*sizeof b[0]);return (int)n;
}

#include <ctype.h>
#include <fcntl.h>
#include <linux/capability.h>
#include <signal.h>
#include <stdlib.h>
#include <sys/prctl.h>
#include <unistd.h>

/* All calls are explicit six-argument Linux syscalls, allowing a test-only linker
 * wrapper to intercept EVERY component call without forwarding security writes. */
#define SC(n,a,b,c,d,e,f) syscall((n),(unsigned long)(a),(unsigned long)(b), \
  (unsigned long)(c),(unsigned long)(d),(unsigned long)(e),(unsigned long)(f))
#define CE_CAPS ((1ULL<<CAP_SETUID)|(1ULL<<CAP_SETGID))
#define CE_STATUS_MAX 8192
struct snapshot {
  uint64_t uid[4],gid[4],cap[5],groups,threads,nnp;
};
static int numbers(char *s,unsigned base,size_t max,uint64_t *v,size_t *count) {
  size_t n=0;
  while(*s) {
    while(*s==' ' || *s=='\t')++s;
    if(!*s)break;
    if(*s=='+' || *s=='-' || n>=max || !isxdigit((unsigned char)*s))return -1;
    errno=0;char *end;
    unsigned long long x=strtoull(s,&end,(int)base);
    if(errno || end==s || (*end && *end!=' ' && *end!='\t'))return -1;
    v[n++]=x;s=end;
  }
  *count=n;return 0;
}
static int parse_status(char *s,struct snapshot *out) {
  static const char *const keys[]={"Uid:","Gid:","Groups:","Threads:","NoNewPrivs:",
                                  "CapInh:","CapPrm:","CapEff:","CapBnd:","CapAmb:"};
  unsigned seen=0;memset(out,0,sizeof *out);
  while(*s) {
    char *end=strchr(s,'\n');if(!end)return -1;
    *end=0;
    for(unsigned i=0;i<10;++i) {
      size_t k=strlen(keys[i]);
      if(strncmp(s,keys[i],k))continue;
      if((seen&(1u<<i)) || (s[k]!=' ' && s[k]!='\t'))return -1;
      uint64_t values[64];size_t n=0;
      unsigned base=i>=5?16:10;
      size_t max=i<2?4:(i==2?64:1);
      if(numbers(s+k,base,max,values,&n))return -1;
      if(i!=2 && n!=max)return -1;
      if(i==0)memcpy(out->uid,values,sizeof out->uid);
      else if(i==1)memcpy(out->gid,values,sizeof out->gid);
      else if(i==2)out->groups=n;
      else if(i==3)out->threads=values[0];
      else if(i==4)out->nnp=values[0];
      else out->cap[i-5]=values[0];
      seen|=1u<<i;break;
    }
    s=end+1;
  }
  return seen==1023?0:-1;
}
/* -2 preserves close uncertainty separately even before credential mutations. */
static int read_snapshot(struct snapshot *out) {
  long fd=SC(SYS_openat,AT_FDCWD,"/proc/self/status",O_RDONLY|O_CLOEXEC|O_NOFOLLOW,0,0,0);
  if(fd<0)return -1;
  char text[CE_STATUS_MAX+2];size_t used=0;int error=0;
  for(;;) {
    long n=SC(SYS_read,fd,text+used,CE_STATUS_MAX+1-used,0,0,0);
    if(n<0){error=1;break;}
    if(!n)break;
    if((size_t)n>CE_STATUS_MAX+1-used){error=1;break;}
    used+=(size_t)n;
    if(used>CE_STATUS_MAX){error=1;break;}
  }
  if(SC(SYS_close,fd,0,0,0,0,0))return -2;
  if(error || !used || memchr(text,0,used))return -1;
  text[used]=0;return parse_status(text,out);
}
static int match(const struct snapshot *s,uint32_t uid,uint32_t gid,int sealed) {
  for(unsigned i=0;i<4;++i)if(s->uid[i]!=uid || s->gid[i]!=gid)return 0;
  if(s->threads!=1 || s->nnp!=1 || (sealed && s->groups))return 0;
  for(unsigned i=0;i<5;++i) {
    uint64_t expected=sealed?(i==3?CE_CAPS:0):CE_CAPS;
    if(s->cap[i]!=expected)return 0;
  }
  return 1;
}
static int seal(struct ce_attempt *attempt,const struct ce_ids *profile,int worker) {
  if(!attempt)return CE_REJECTED;
  if(atomic_exchange_explicit(&attempt->consumed,1,memory_order_acq_rel))
    return CE_ALREADY_ATTEMPTED;
  if(!valid_ids(profile))return CE_REJECTED;
  struct ce_ids p=*profile;struct snapshot before,after;
  int r=read_snapshot(&before);
  if(r==-2)return CE_UNKNOWN;
  if(r || !match(&before,p.owner_uid,p.owner_gid,0))return CE_REJECTED;
  struct sock_filter filter[CE_FILTER_MAX];
  int n=ce_build_id_filter(&p,filter,CE_FILTER_MAX);
  if(n<=0)return CE_REJECTED;
  struct sock_fprog program={(unsigned short)n,filter};
  /* Attempt consumed BEFORE installing any mutation; errors never retry. */
  if(SC(SYS_seccomp,SECCOMP_SET_MODE_FILTER,0,&program,0,0,0))return CE_UNKNOWN;
  if(SC(SYS_setgroups,0,NULL,0,0,0,0))return CE_UNKNOWN;
  if(worker) {
    if(SC(SYS_setresgid,p.worker_gid,p.worker_gid,p.worker_gid,0,0,0))return CE_UNKNOWN;
    if(SC(SYS_setresuid,p.worker_uid,p.worker_uid,p.worker_uid,0,0,0))return CE_UNKNOWN;
  }
  if(SC(SYS_prctl,PR_CAP_AMBIENT,PR_CAP_AMBIENT_CLEAR_ALL,0,0,0,0))return CE_UNKNOWN;
  struct __user_cap_header_struct header={_LINUX_CAPABILITY_VERSION_3,0};
  struct __user_cap_data_struct zero[2]={{0,0,0},{0,0,0}};
  if(SC(SYS_capset,&header,zero,0,0,0,0))return CE_UNKNOWN;
  if(worker) {
    if(SC(SYS_prctl,PR_SET_PDEATHSIG,SIGKILL,0,0,0,0))return CE_UNKNOWN;
    int signal=0;
    if(SC(SYS_prctl,PR_GET_PDEATHSIG,&signal,0,0,0,0) || signal!=SIGKILL)
      return CE_UNKNOWN;
  }
  if(read_snapshot(&after))return CE_UNKNOWN;
  if(!match(&after,worker?p.worker_uid:p.owner_uid,
                   worker?p.worker_gid:p.owner_gid,1))return CE_UNKNOWN;
  /* Credentials only: NOT parent custody, exec-entry proof, F1, or RUN authority. */
  return CE_SEALED_CREDENTIALS_ONLY;
}
int ce_seal_worker(struct ce_attempt *a,const struct ce_ids *p) {return seal(a,p,1);}
int ce_seal_owner(struct ce_attempt *a,const struct ce_ids *p) {return seal(a,p,0);}
