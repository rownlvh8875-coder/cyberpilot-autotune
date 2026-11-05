/* TEST ONLY. Fixed failure cases; no runtime fault/callback API. */
#define main ci_fixture_main
#include "../../research/cohort_integration/cohort.c"
#undef main
#include <stdarg.h>
#include <dirent.h>
#include <sys/mman.h>
struct test_audit {atomic_uint births[3],waits[3],execs,starts,unrefs;};
static struct test_audit *audit;
const char *fm_test_case="normal";
const char *entry_case="normal";
static int context_clock_armed,context_clock_fired;
static int role,grant_fd=-1,close_fired,shutdown_fd=-1;
static int foreign_fd=-1,foreign_anchor=-1;
static int named(const char *s){return !strcmp(entry_case,s);}
ssize_t __real_sendmsg(int,const struct msghdr *,int);
ssize_t __real_recvmsg(int,struct msghdr *,int);
int __real_close(int);
int __real_waitid(idtype_t,id_t,siginfo_t *,int);
long __real_syscall(long,...);
int __real_mkdirat(int,const char *,mode_t);
int __wrap_mkdirat(int fd,const char *name,mode_t mode) {
 int r=__real_mkdirat(fd,name,mode);
 if(!r && role==0)context_clock_armed=1;
 return r;
}
int __real_clock_gettime(clockid_t,struct timespec *);
int __wrap_clock_gettime(clockid_t id,struct timespec *t) {
 if(role==0 && named("context_clock_once") && context_clock_armed && !context_clock_fired++) {
  errno=EIO;return -1;
 }
 return __real_clock_gettime(id,t);
}
static void replace_parent_name(void) {
 DIR *d=opendir("lab-fixtures");struct dirent *e;
 if(!d)_exit(96);
 while((e=readdir(d))) {
  if(strncmp(e->d_name,"parent-",7))continue;
  char path[300];snprintf(path,sizeof path,"lab-fixtures/%s",e->d_name);
  if(rename(path,"lab-fixtures/retained-original") || mkdir(path,0700))_exit(96);
  break;
 }
 if(closedir(d))_exit(96);
}
ssize_t __wrap_sendmsg(int fd,const struct msghdr *m,int flags) {
 const unsigned char *p=m->msg_iov[0].iov_base;
 size_t size=m->msg_iov[0].iov_len;
 if(size>=4+CTX && !memcmp(p+4,"NPG1",4)) {
  if(role==0 && p[9]==3) {
   struct cmsghdr *h=CMSG_FIRSTHDR((struct msghdr *)m);
   if(!h)_exit(96);
   memcpy(&grant_fd,CMSG_DATA(h),sizeof grant_fd);
   if(named("parent_name_replaced"))replace_parent_name();
   if(named("parent_fd_reused")) {
    foreign_anchor=fcntl(grant_fd,F_DUPFD_CLOEXEC,3);
    if(__real_close(grant_fd))_exit(96);
    int n=open("/dev/null",O_RDONLY|O_CLOEXEC);
    if(n!=grant_fd){if(dup2(n,grant_fd)!=grant_fd)_exit(96);__real_close(n);}
    foreign_fd=grant_fd;
   }
   if(!strncmp(entry_case,"grant_",6)) {
    unsigned char data[MAX_FRAME+4];memcpy(data,p,size);
    if(named("grant_nonce"))data[53]^=1;
    if(named("grant_generation"))data[21]^=1;
    if(named("grant_cohort"))data[22]^=1;
    if(named("grant_sequence"))data[13]^=1;
    if(named("grant_empty"))memset(data,0,4);
    if(named("grant_oversize")){uint32_t n=htonl(513);memcpy(data,&n,4);}
    if(named("grant_partial"))size=5;
    struct iovec io={data,size};struct msghdr copy=*m;copy.msg_iov=&io;
    if(named("grant_no_fd")){copy.msg_control=NULL;copy.msg_controllen=0;}
    union {struct cmsghdr h;char b[CMSG_SPACE(2*sizeof(int))];} control={0};
    int wrong=-1;
    if(named("grant_extra_fd") || named("grant_wrong_type")) {
     int fds[2]={grant_fd,grant_fd};
     if(named("grant_wrong_type")){wrong=open("/dev/null",O_RDONLY|O_CLOEXEC);fds[0]=wrong;}
     copy.msg_control=control.b;copy.msg_controllen=CMSG_SPACE(named("grant_extra_fd")?2*sizeof(int):sizeof(int));
     struct cmsghdr *ch=CMSG_FIRSTHDR(&copy);ch->cmsg_level=SOL_SOCKET;ch->cmsg_type=SCM_RIGHTS;
     ch->cmsg_len=CMSG_LEN(named("grant_extra_fd")?2*sizeof(int):sizeof(int));
     memcpy(CMSG_DATA(ch),fds,named("grant_extra_fd")?2*sizeof(int):sizeof(int));
    }
    ssize_t r=__real_sendmsg(fd,&copy,flags);if(wrong>=0)__real_close(wrong);return r;
   }
  }
  if(role==0 && p[9]==5) {
   if(named("commit_duplicate")) {
    ssize_t r=__real_sendmsg(fd,m,flags);
    if(r!=(ssize_t)size)return r;
    return __real_sendmsg(fd,m,flags);
   }
   if(named("commit_extra")) {
    ssize_t r=__real_sendmsg(fd,m,flags);
    unsigned char x=1;if(send(fd,&x,1,MSG_NOSIGNAL)!=1)_exit(96);
    return r;
   }
  }
  if(role==2 && p[9]==2 && named("ready_early_eof"))return (ssize_t)size;
  if(role==2 && p[9]==6) {
   if(named("final_ack_error")){errno=EIO;return -1;}
   if(named("final_no_shutdown"))shutdown_fd=fd;
   if(named("final_extra")) {
    ssize_t r=__real_sendmsg(fd,m,flags);
    unsigned char x=1;if(send(fd,&x,1,MSG_NOSIGNAL)!=1)_exit(96);
    return r;
   }
  }
 }
 return __real_sendmsg(fd,m,flags);
}
int __real_shutdown(int,int);
int __wrap_shutdown(int fd,int how) {
 if(fd==shutdown_fd && named("final_no_shutdown"))return 0;
 return __real_shutdown(fd,how);
}
ssize_t __wrap_recvmsg(int fd,struct msghdr *m,int flags) {
 ssize_t n=__real_recvmsg(fd,m,flags);
 if(n<0)return n;
 if(role==2 && named("worker_wrong_sender"))
  for(struct cmsghdr *h=CMSG_FIRSTHDR(m);h;h=CMSG_NXTHDR(m,h))
   if(h->cmsg_level==SOL_SOCKET && h->cmsg_type==SCM_CREDENTIALS)
    ((struct ucred *)CMSG_DATA(h))->pid+=1;
 return n;
}
int __wrap_close(int fd) {
 if(role==0 && fd==foreign_fd)_exit(98);
 int r=__real_close(fd);
 if(role==0 && fd==grant_fd && named("parent_close_unknown") && !close_fired++) {
  errno=EINTR;return -1;
 }
 return r;
}
int __wrap_waitid(idtype_t t,id_t id,siginfo_t *info,int flags) {
 if(role<3)atomic_fetch_add(&audit->waits[role],1);
 int r=__real_waitid(t,id,info,flags);
 if((role==0 && named("factory_wait_unknown")) ||
    (role==1 && named("manager_wait_unknown")) || (role==2 && named("worker_wait_unknown"))) {
  errno=EINTR;return -1;
 }
 return r;
}
long __wrap_syscall(long nr,...) {
 va_list ap;va_start(ap,nr);unsigned long a[6]={0};unsigned count;
 switch(nr) {
 case SYS_kcmp:case SYS_execveat:count=5;break;
 case SYS_clone3:case SYS_pidfd_open:case SYS_memfd_create:count=2;break;
 case SYS_close_range:count=3;break;case SYS_pidfd_send_signal:count=4;break;
 default:_exit(96);
 }
 for(unsigned i=0;i<count;++i)a[i]=va_arg(ap,unsigned long);
 va_end(ap);
 if(nr==SYS_execveat)atomic_fetch_add(&audit->execs,1);
 if(nr==SYS_execveat && named("worker_exec_error")){errno=ENOEXEC;return -1;}
 long r=__real_syscall(nr,a[0],a[1],a[2],a[3],a[4],a[5]);
 if(nr==SYS_clone3 && r>0 && role<3)atomic_fetch_add(&audit->births[role],1);
 if(nr==SYS_clone3 && r==0)++role;
 if(nr==SYS_clone3 && r>0 && ((role==1 && named("cancel_e_birth")) ||
    (role==2 && named("cancel_w_birth")))){errno=ECANCELED;return -1;}
 return r;
}
int __real_sd_bus_call(sd_bus *,sd_bus_message *,uint64_t,sd_bus_error *,sd_bus_message **);
int __wrap_sd_bus_call(sd_bus *b,sd_bus_message *m,uint64_t timeout,sd_bus_error *error,sd_bus_message **reply) {
 const char *member=sd_bus_message_get_member(m);
 if(role==0 && member) {
  if(!strcmp(member,"StartTransientUnit"))atomic_fetch_add(&audit->starts,1);
  if(!strcmp(member,"UnrefUnit"))atomic_fetch_add(&audit->unrefs,1);
 }
 return __real_sd_bus_call(b,m,timeout,error,reply);
}
static void print_audit(void) {
 printf("{\"audit\":{\"births\":[%u,%u,%u],\"waits\":[%u,%u,%u],"
  "\"exec_attempts\":%u,\"start_attempts\":%u,\"unrefs\":%u}}\n",
  atomic_load(&audit->births[0]),atomic_load(&audit->births[1]),atomic_load(&audit->births[2]),
  atomic_load(&audit->waits[0]),atomic_load(&audit->waits[1]),atomic_load(&audit->waits[2]),
  atomic_load(&audit->execs),atomic_load(&audit->starts),atomic_load(&audit->unrefs));
}
int main(int argc,char **argv) {
 if(argc!=2)return 96;
 entry_case=fm_test_case=argv[1];
 audit=mmap(NULL,sizeof *audit,PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);
 if(audit==MAP_FAILED)return 96;
 int r=ci_fixture_main();
 if(foreign_fd>=0) {
  if(fcntl(foreign_fd,F_GETFD)<0 || fcntl(foreign_anchor,F_GETFD)<0)_exit(98);
  __real_close(foreign_fd);__real_close(foreign_anchor);
 }
 if(named("twice"))r=ci_fixture_main();
 print_audit();
 if(munmap(audit,sizeof *audit))return 96;
 return r;
}
