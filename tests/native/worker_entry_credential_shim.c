/* TEST ONLY: no syscall forwarding. All security writes are simulated. */
#define _GNU_SOURCE
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/syscall.h>
#include <sys/prctl.h>
#include <signal.h>
extern const char *entry_case;
static unsigned uid=17001,gid=17002,sealed,worker,filters,offset;
static char status[1024];
static int named(const char *s) {return !strcmp(entry_case,s);}
long entry_test_syscall(long nr,...) {
 va_list ap;va_start(ap,nr);unsigned long a[6];
 for(unsigned i=0;i<6;++i)a[i]=va_arg(ap,unsigned long);
 va_end(ap);
 if(nr==SYS_openat) {
  if(strcmp((char *)a[1],"/proc/self/status"))goto denied;
  unsigned cap=sealed?0:192;
  snprintf(status,sizeof status,
    "Uid:\t%u %u %u %u\nGid:\t%u %u %u %u\nGroups:\t%s\nThreads:\t1\n"
    "NoNewPrivs:\t1\nCapInh:\t%x\nCapPrm:\t%x\nCapEff:\t%x\nCapBnd:\tc0\nCapAmb:\t%x\n",
    uid,uid,uid,uid,gid,gid,gid,gid,sealed?"":"17002",cap,cap,cap,cap);
  offset=0;return 1000000;
 }
 if(nr==SYS_read) {
  if(a[0]!=1000000)goto denied;
  size_t n=strlen(status)-offset;
  if(n>a[2])n=a[2];
  memcpy((void *)a[1],status+offset,n);offset+=(unsigned)n;return (long)n;
 }
 if(nr==SYS_close && a[0]==1000000)return 0;
 if(nr==SYS_seccomp) {
  ++filters;if(named("prebirth_filter") && filters==1)goto denied;return 0;
 }
 if(nr==SYS_setgroups)return a[0] || a[1]?-1:0;
 if(nr==SYS_setresgid){gid=(unsigned)a[0];return 0;}
 if(nr==SYS_setresuid){uid=(unsigned)a[0];worker=1;return 0;}
 if(nr==SYS_capset) {
  if((worker && named("worker_seal")) || (!worker && named("owner_seal")))goto denied;
  sealed=1;return 0;
 }
 if(nr==SYS_prctl) {
  if(a[0]==PR_GET_PDEATHSIG)*(int *)a[1]=SIGKILL;
  else if(a[0]!=PR_SET_PDEATHSIG && a[0]!=PR_CAP_AMBIENT)goto denied;
  return 0;
 }
denied:
 errno=EPERM;return -1;
}
