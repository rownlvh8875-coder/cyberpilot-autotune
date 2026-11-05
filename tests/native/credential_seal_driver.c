#define _GNU_SOURCE
#include "seal.h"
#include <errno.h>
#include <linux/capability.h>
#include <linux/seccomp.h>
#include <signal.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>

/* No __real_syscall symbol: any unexpected component syscall aborts the fixture. */
static struct ce_ids ids = {17001, 17002, 18001, 18002};
static unsigned long uid[4] = {17001,17001,17001,17001};
static unsigned long gid[4] = {17002,17002,17002,17002};
static unsigned long caps=192, ambient=192, groups=1;
static int writes=0, fail_at=0, pdeath=0;
static int all_calls=0,close_calls=0,nested_result=-1,nested_calls=-1,nested_writes=-1;
static struct ce_attempt *live_attempt;
static const char *scenario="normal";
static char trace[256], status[10000];
static size_t offset=0, status_len=0;
static int is(const char *s) {return !strcmp(scenario,s);}
static int mutation(const char *name) {
  if(trace[0])strcat(trace,",");
  strcat(trace,name);++writes;
  if(!strcmp(scenario,"reentrant") && writes==1) {
    int c=all_calls,w=writes;
    nested_result=ce_seal_owner(live_attempt,&ids);
    nested_calls=all_calls-c;nested_writes=writes-w;
  }
  if(writes==fail_at){errno=EINTR;return -1;}
  return 0;
}
static void snapshot(void) {
  unsigned long u[4],g[4];memcpy(u,uid,sizeof u);memcpy(g,gid,sizeof g);
  unsigned long c=caps,a=ambient,gr=groups;int nnp=1,threads=1;
  if(!writes) {
    if(is("initial_uid"))u[0]=999;
    if(is("initial_caps"))c|=1;
    if(is("initial_ambient"))a=0;
    if(is("initial_nnp"))nnp=0;
    if(is("threads"))threads=2;
  } else {
    if(is("saved_uid"))u[2]=17001;
    if(is("fs_uid"))u[3]=17001;
    if(is("saved_gid"))g[2]=17002;
    if(is("fs_gid"))g[3]=17002;
    if(is("post_caps"))c=64;
    if(is("post_ambient"))a=64;
    if(is("post_groups"))gr=1;
    if(is("post_nnp"))nnp=0;
  }
  int n=snprintf(status,sizeof status,
    "Name:\tfixed-synthetic\nUid:\t%lu %lu %lu %lu\nGid:\t%lu %lu %lu %lu\n"
    "Groups:\t%s\nThreads:\t%d\nNoNewPrivs:\t%d\n"
    "CapInh:\t%016lx\nCapPrm:\t%016lx\nCapEff:\t%016lx\nCapBnd:\t00000000000000c0\nCapAmb:\t%016lx\n",
    u[0],u[1],u[2],u[3],g[0],g[1],g[2],g[3],gr?"17002":"",threads,nnp,c,c,c,a);
  if(n<0 || (size_t)n>=sizeof status)_exit(93);
  if((!writes && is("missing")) || (writes && is("post_missing"))) {
    char *x=strstr(status,"CapAmb:");if(x)*x=0;
  }
  if((!writes && is("duplicate")) || (writes && is("post_duplicate")))
    strcat(status,"Uid:\t1 1 1 1\n");
  if(!writes && is("oversize"))memset(status,'x',sizeof status-1);
  status[sizeof status-1]=0;status_len=strlen(status);offset=0;
}
long __wrap_syscall(long nr, ...) {
  ++all_calls;va_list ap;va_start(ap,nr);
  unsigned long a[6];for(int i=0;i<6;++i)a[i]=va_arg(ap,unsigned long);va_end(ap);
  if(nr==SYS_openat) {
    if(strcmp((const char *)a[1],"/proc/self/status"))_exit(94);
    if(writes && is("post_open_error")){errno=EIO;return -1;}
    snapshot();return 97;
  }
  if(nr==SYS_read) {
    if(a[0]!=97)_exit(95);
    if(is("read_error") || (writes && is("post_read_error"))){errno=EIO;return -1;}
    size_t n=status_len-offset;if(n>a[2])n=a[2];
    memcpy((void *)a[1],status+offset,n);offset+=n;return (long)n;
  }
  if(nr==SYS_close) {
    ++close_calls;if(a[0]!=97)_exit(96);
    if((!writes && is("pre_close_error")) || (writes && is("post_close_error"))) {
      errno=EINTR;return -1;
    }
    return 0;
  }
  if(nr==SYS_seccomp) {
    if(a[0]!=SECCOMP_SET_MODE_FILTER || a[1]!=0)_exit(97);
    const struct sock_fprog *p=(const void *)a[2];if(!p || !p->len)_exit(98);
    return mutation("filter");
  }
  if(nr==SYS_setgroups) {if(a[0] || a[1])_exit(99);groups=0;return mutation("groups");}
  if(nr==SYS_setresgid) {
    for(int i=0;i<3;++i)gid[i]=a[i];
    gid[3]=a[1];return mutation("gid");
  }
  if(nr==SYS_setresuid) {
    for(int i=0;i<3;++i)uid[i]=a[i];
    uid[3]=a[1];return mutation("uid");
  }
  if(nr==SYS_capset) {
    const struct __user_cap_header_struct *h=(const void *)a[0];
    const struct __user_cap_data_struct *d=(const void *)a[1];
    if(h->version!=_LINUX_CAPABILITY_VERSION_3 || h->pid ||
       d[0].effective || d[0].permitted || d[0].inheritable ||
       d[1].effective || d[1].permitted || d[1].inheritable)_exit(100);
    caps=0;return mutation("capclear");
  }
  if(nr==SYS_prctl) {
    if(a[0]==PR_CAP_AMBIENT && a[1]==PR_CAP_AMBIENT_CLEAR_ALL) {
      ambient=0;return mutation("ambient");
    }
    if(a[0]==PR_SET_PDEATHSIG) {if(a[1]!=SIGKILL)_exit(101);pdeath=SIGKILL;return mutation("pdeath");}
    if(a[0]==PR_GET_PDEATHSIG) {
      if(is("pdeath_query_error")){errno=EIO;return -1;}
      *(int *)a[1]=is("pdeath_wrong")?0:pdeath;return 0;
    }
  }
  _exit(102);
}
int main(int argc,char **argv) {
  if(argc!=5)return 2;
  scenario=argv[2];fail_at=atoi(argv[3]);
  /* pytest passes four arguments, argv[4] is an explicit fixture marker. */
  if(strcmp(argv[4],"fixture"))return 2;
  if(!strcmp(argv[1],"filter")) {
    struct sock_filter out[CE_FILTER_MAX];
    int n=ce_build_id_filter(&ids,out,CE_FILTER_MAX);if(n<=0)return 3;
    for(int i=0;i<n;++i)printf("%u,%u,%u,%u\n",out[i].code,out[i].jt,out[i].jf,out[i].k);
    return 0;
  }
  if(is("bad_profile"))ids.worker_uid=0;
  struct ce_attempt attempt=CE_ATTEMPT_INIT;live_attempt=&attempt;
  int worker=!strcmp(argv[1],"worker");
  int result=worker?ce_seal_worker(&attempt,&ids):ce_seal_owner(&attempt,&ids);
  int before=writes,calls_before=all_calls;
  int repeat=worker?ce_seal_worker(&attempt,&ids):ce_seal_owner(&attempt,&ids);
  printf("result=%d\nrepeat=%d\nrepeat_writes=%d\nwrites=%d\nuid=%lu\ncap=%lu\ngroups=%lu\ntrace=%s\n",
    result,repeat,writes-before,writes,uid[0],caps,groups,trace);
  printf("close_calls=%d\nrepeat_calls=%d\nnested_result=%d\nnested_calls=%d\nnested_writes=%d\n",
    close_calls,all_calls-calls_before,nested_result,nested_calls,nested_writes);
  return 0;
}
