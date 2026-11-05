/* TEST ONLY: fixed cases, no production fault environment/API. */
#define ENTRY_CREDENTIAL_BOUNDARY "SIMULATED"
#define main fixed_entry_main
#include "../../research/worker_entry/integration.c"
#undef main
#include <stdarg.h>
const char *entry_case="normal";
static int once,seen_entry,closed_once,role,foreign_fd=-1,received_fd=-1,received_closes;
static unsigned char previous_entry[MAX_FRAME];
static size_t previous_size;
static pid_t factory;
static int worker_parent_polls;
static int named(const char *s){return !strcmp(entry_case,s);}
ssize_t __real_sendmsg(int,const struct msghdr *,int);
ssize_t __real_recvmsg(int,struct msghdr *,int);
int __real_close(int);
int __real_waitid(idtype_t,id_t,siginfo_t *,int);
long __real_syscall(long,...);
int __real_poll(struct pollfd *,nfds_t,int);
int __real_clock_gettime(clockid_t,struct timespec *);
int __wrap_clock_gettime(clockid_t id,struct timespec *t) {
 if(named("clock_unavailable")){errno=EIO;return -1;}
 return __real_clock_gettime(id,t);
}
int __wrap_poll(struct pollfd *p,nfds_t n,int ms) {
 if(role==2) {++worker_parent_polls;
  if(named("owner_dead") || (named("owner_dead_late") && worker_parent_polls==2))return 1;
 }
 return __real_poll(p,n,ms);
}
int __wrap___poll_chk(struct pollfd *p,nfds_t n,int ms,size_t capacity) {
 if(n>capacity/sizeof *p){errno=EINVAL;return -1;}
 return __wrap_poll(p,n,ms);
}
ssize_t __wrap_sendmsg(int fd,const struct msghdr *m,int flags) {
 const unsigned char *p=m->msg_iov[0].iov_base;
 if(named("final_ack") && m->msg_iov[0].iov_len>=4+CTX &&
    !memcmp(p+4,"NPG1",4) && p[9]==6){errno=EIO;return -1;}
 if(m->msg_iov[0].iov_len>=4+CTX && !memcmp(p+4,"NWE1",4) && p[9]==1) {
  if(!strncmp(entry_case,"bind_",5)) {
   unsigned char altered[MAX_FRAME+4];size_t size=m->msg_iov[0].iov_len;
   memcpy(altered,p,size);
   if(named("bind_magic"))altered[4]^=1;
   if(named("bind_stage"))altered[9]=9;
   if(named("bind_sequence"))altered[13]=1;
   if(named("bind_parent"))altered[4+CTX+3]^=1;
   if(named("bind_empty"))memset(altered,0,4);
   if(named("bind_oversize")){uint32_t v=htonl(513);memcpy(altered,&v,4);}
   if(named("bind_partial"))size=5;
   struct iovec io={altered,size};struct msghdr copy=*m;copy.msg_iov=&io;
   return __real_sendmsg(fd,&copy,flags);
  }
  if(named("rights")) {
   union {struct cmsghdr h;char b[CMSG_SPACE(sizeof(int))];} control={0};
   struct msghdr copy=*m;copy.msg_control=control.b;copy.msg_controllen=sizeof control;
   struct cmsghdr *h=CMSG_FIRSTHDR(&copy);h->cmsg_level=SOL_SOCKET;
   h->cmsg_type=SCM_RIGHTS;h->cmsg_len=CMSG_LEN(sizeof(int));
   int grant=0;memcpy(CMSG_DATA(h),&grant,sizeof grant);
   return __real_sendmsg(fd,&copy,flags);
  }
 }
 if(m->msg_iov[0].iov_len>=4+CTX && !memcmp(p+4,"NWE1",4) && p[9]==3 &&
    (!strcmp(entry_case,"finish_nonce") || !strcmp(entry_case,"finish_sequence"))) {
  unsigned char altered[MAX_FRAME+4];size_t size=m->msg_iov[0].iov_len;
  memcpy(altered,p,size);altered[named("finish_nonce")?53:13]^=1;
  struct iovec io={altered,size};struct msghdr copy=*m;copy.msg_iov=&io;
  return __real_sendmsg(fd,&copy,flags);
 }
 return __real_sendmsg(fd,m,flags);
}
ssize_t __wrap_recvmsg(int fd,struct msghdr *m,int flags) {
 ssize_t n=__real_recvmsg(fd,m,flags);
 if(n<0)return n;
 int worker_message=0;
 for(struct cmsghdr *h=CMSG_FIRSTHDR(m);h;h=CMSG_NXTHDR(m,h)) {
  if(h->cmsg_level==SOL_SOCKET && h->cmsg_type==SCM_CREDENTIALS) {
   worker_message=1;struct ucred *u=(struct ucred *)CMSG_DATA(h);
   if(named("wrong_sender"))u->pid=(pid_t)(u->pid+1);
   if(named("credentials_uid"))u->uid=(uid_t)(u->uid+1);
   if(named("credentials_gid"))u->gid=(gid_t)(u->gid+1);
  }
 }
 if(worker_message && n>0 && named("missing_credentials"))m->msg_controllen=0;
 unsigned char *b=m->msg_iov[0].iov_base;
 if(worker_message && n==4 && !once) {
  if(named("empty")){memset(b,0,4);once=1;}
  if(named("oversize")){uint32_t v=htonl(513);memcpy(b,&v,4);once=1;}
  if(named("partial_prefix")){once=1;return 2;}
 }
 if(worker_message && n>=CTX && !memcmp(b,"NWE1",4) && b[5]==2) {
  seen_entry=1;
  memcpy(previous_entry,b,(size_t)n);previous_size=(size_t)n;
  if(named("nonce"))b[49]^=1;
  if(named("generation"))b[17]^=1;
  if(named("cohort"))b[18]^=1;
  if(named("sequence"))b[9]^=1;
  if(named("stage"))b[5]=9;
  if(named("image_identity"))b[CTX+15]^=1;
  if(named("parent_identity"))b[CTX+19]^=1;
  if(named("fd_mask"))b[CTX+31]^=16;
  if(named("partial_body"))return n-1;
 }
 if(worker_message && n>=CTX && b[5]==4 && named("duplicate")) {
  memcpy(b,previous_entry,(size_t)n<previous_size?(size_t)n:previous_size);
 }
 if(worker_message && n==0 && named("eof_credentials")) {
  struct cmsghdr *h=CMSG_FIRSTHDR(m);if(h)((struct ucred *)CMSG_DATA(h))->pid=1;
 }
 if(worker_message && n>0 && named("truncated_control"))m->msg_flags|=MSG_CTRUNC;
 if(worker_message && n>0 && named("duplicate_credentials")) {
  size_t len=CMSG_SPACE(sizeof(struct ucred));
  memcpy((char *)m->msg_control+len,m->msg_control,len);m->msg_controllen=2*len;
 }
 if(worker_message && n>0 && named("received_rights") && received_fd<0) {
  size_t len=CMSG_SPACE(sizeof(struct ucred));
  received_fd=open("/dev/null",O_RDONLY|O_CLOEXEC);
  struct cmsghdr *h=(struct cmsghdr *)((char *)m->msg_control+len);
  h->cmsg_level=SOL_SOCKET;h->cmsg_type=SCM_RIGHTS;h->cmsg_len=CMSG_LEN(sizeof(int));
  memcpy(CMSG_DATA(h),&received_fd,sizeof received_fd);
  m->msg_controllen=len+CMSG_SPACE(sizeof(int));
 }
 if(worker_message && seen_entry && named("image_reuse") && foreign_fd<0) {
  /* Locate the memfd via its exact creation name in this fixed fixture only. */
  for(int q=3;q<32;++q) {
   char name[64],path[64];snprintf(path,sizeof path,"/proc/self/fd/%d",q);
   ssize_t size=readlink(path,name,sizeof name-1);
   if(size>0){name[size]=0;if(strstr(name,"memfd:fixed-synthetic-worker")) {
    __real_close(q);int d=open(".",O_DIRECTORY|O_RDONLY);
    if(d!=q){if(dup2(d,q)!=q)_exit(96);__real_close(d);}
    foreign_fd=q;break;
   }}
  }
 }
 if(worker_message && n==0 && named("extra")){b[0]=42;return 1;}
 return n;
}
int __wrap_close(int fd) {
 if(fd==foreign_fd)_exit(98);
 if(fd==received_fd)++received_closes;
 int r=__real_close(fd);
 if(named("close_unknown") && getpid()!=factory && seen_entry && !closed_once++) {
  errno=EINTR;return -1;
 }
 return r;
}
int __wrap_waitid(idtype_t t,id_t id,siginfo_t *info,int options) {
 if(named("received_rights") && received_fd>=0 && received_closes!=1)_exit(98);
 if(named("wait_unknown") && getpid()!=factory){errno=EINTR;return -1;}
 int result=__real_waitid(t,id,info,options);
 if(named("unknown_owner_exit") && getpid()==factory && !result) {
  info->si_code=CLD_KILLED;info->si_status=SIGKILL;
 }
 return result;
}
long __wrap_syscall(long nr,...) {
 va_list ap;va_start(ap,nr);unsigned long a[6]={0};
 unsigned count=0;
 switch(nr) {
 case SYS_kcmp:count=5;break;
 case SYS_clone3:case SYS_pidfd_open:case SYS_memfd_create:count=2;break;
 case SYS_close_range:count=3;break;
 case SYS_pidfd_send_signal:count=4;break;
 case SYS_execveat:count=5;break;
 default:_exit(96);
 }
 for(unsigned i=0;i<count;++i)a[i]=va_arg(ap,unsigned long);
 va_end(ap);
 if(nr==SYS_execveat) {
  if(named("preexec_message")) {
   /* False exec-pipe EOF + same original PID does not prove exec by itself. */
   __real_close(5);
   struct channel c={.fd=-1,.anchor=-1};struct frame f={0};struct stat st;
   unsigned char wire[CTX+32];
   int self=open("/proc/self/exe",O_RDONLY);
   if(channel_init(&c,3) || read_frame(&c,&f,0) || fstat(self,&st))_exit(71);
   message(wire,f.data,2,1);write64(wire+CTX,st.st_dev);write64(wire+CTX+8,st.st_ino);
   put32(wire+CTX+16,(uint32_t)getppid());put32(wire+CTX+20,getuid());
   put32(wire+CTX+24,getgid());put32(wire+CTX+28,15);
   (void)send_frame(&c,wire,sizeof wire,-1);_exit(71);
  }
  if(named("exec_error")){errno=ENOEXEC;return -1;}
  if(named("early_exit"))_exit(71);
 }
 if(nr==SYS_close_range && named("leaked_directory") && getpid()!=factory && a[0]==7) {
  /* Preserve a deliberately inherited directory, forcing W entry rejection. */
  int leak=open(".",O_RDONLY|O_DIRECTORY);
  if(leak<0)_exit(96);
  if(dup2(leak,7)!=7)_exit(96);
  a[0]=8;
 }
 if(nr==SYS_clone3 && role==1 && named("path_replaced")) {
  char path[4096];ssize_t size=readlink("/proc/self/exe",path,sizeof path-1);
  if(size<=0)_exit(96);
  path[size]=0;
  char *last=strrchr(path,'/');if(!last)_exit(96);strcpy(last+1,"fixed-worker");
  int fd=open(path,O_WRONLY|O_TRUNC);if(fd<0 || write(fd,"bad",3)!=3)_exit(96);
  __real_close(fd);
 }
 long result=__real_syscall(nr,a[0],a[1],a[2],a[3],a[4],a[5]);
 if(nr==SYS_clone3 && result==0)++role;
 if(nr==SYS_clone3 && result>0 &&
    ((role==0 && named("cancel_birth")) || (role==1 && named("cancel_worker_birth")))) {
  errno=ECANCELED;return -1;
 }
 return result;
}
int main(int argc,char **argv) {
 if(argc!=2)return 96;
 entry_case=argv[1];factory=getpid();
 if(named("recv_error_probe")) {
  union {struct cmsghdr h;char b[CMSG_SPACE(sizeof(struct ucred))];} control={0};
  struct msghdr m={0};char byte;struct iovec io={&byte,1};
  m.msg_iov=&io;m.msg_iovlen=1;m.msg_control=control.b;m.msg_controllen=sizeof control;
  struct cmsghdr *h=CMSG_FIRSTHDR(&m);h->cmsg_level=SOL_SOCKET;h->cmsg_type=SCM_CREDENTIALS;
  h->cmsg_len=CMSG_LEN(sizeof(struct ucred));
  struct ucred *u=(struct ucred *)CMSG_DATA(h);u->uid=777;
  entry_case="credentials_uid";
  ssize_t n=__wrap_recvmsg(-1,&m,0);
  printf("{\"error_return\":%s,\"control_unchanged\":%s}\n",n==-1?"true":"false",u->uid==777?"true":"false");
  return 0;
 }
 if(named("seal_probe")) {
  struct stat st;int fd=sealed_worker(&st);if(fd<0)return 96;
  errno=0;int wr=pwrite(fd,"x",1,0)==-1 && errno==EPERM;
  errno=0;int tr=ftruncate(fd,0)==-1 && errno==EPERM;close_one(&fd);
  printf("{\"write_rejected\":%s,\"truncate_rejected\":%s}\n",wr?"true":"false",tr?"true":"false");
  return wr && tr?0:96;
 }
 return fixed_entry_main();
}
