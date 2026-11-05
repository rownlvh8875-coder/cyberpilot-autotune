#define _GNU_SOURCE
#define main parent_handoff_fixed_main
#include "../../research/parent_handoff/handoff.c"
#undef main
#include <stdlib.h>
#include <stdarg.h>

static const char *fault="normal";
static pid_t factory;
static int delivered[128],consumed[128],anchors[128],deliveries,remembered_parent=-1,double_injected=0;
static int foreign=-1,reused=-1,closed_seen=0,done_fault=0,close_faulted=0;
ssize_t __real_sendmsg(int,const struct msghdr *,int);
int __real_close(int);
int __real_fcntl(int,int,...);
void __real__exit(int) __attribute__((noreturn));
static void check_received(void) {
  for(int i=0;i<deliveries;++i)if(consumed[i]!=1) {
    fprintf(stderr,"received descriptor not consumed exactly once\n");__real__exit(98);
  }
  for(int i=0;i<deliveries;++i)if(anchors[i]>=0) {
    __real_close(anchors[i]);anchors[i]=-1;
  }
}
void __wrap__exit(int status) __attribute__((noreturn));
void __wrap__exit(int status) {check_received();__real__exit(status);}
int __wrap_fcntl(int fd,int command,...) {
  if(command==F_GETFD) {
    if(getpid()!=factory && !strcmp(fault,"getfd_error")){errno=EINTR;return -1;}
    if(getpid()!=factory && !strcmp(fault,"no_cloexec"))return 0;
    return __real_fcntl(fd,command);
  }
  if(command==F_DUPFD_CLOEXEC) {
    va_list ap;va_start(ap,command);int n=va_arg(ap,int);va_end(ap);
    return __real_fcntl(fd,command,n);
  }
  __real__exit(97);
}
ssize_t __real_recvmsg(int,struct msghdr *,int);
int __real_shutdown(int,int);
int __real_close(int);
int __real_waitid(idtype_t,id_t,siginfo_t *,int);
int __real_fstatfs(int,struct statfs *);

static int is(const char *s){return !strcmp(fault,s);}
int __wrap_fstatfs(int fd,struct statfs *st) {
  int r=__real_fstatfs(fd,st);
  if(!r && getpid()==factory && (is("forbidden_fs") || is("forbidden_fs_v1")))st->f_type=is("forbidden_fs_v1")?0x27e0ebUL:0x63677270UL;
  return r;
}
ssize_t __wrap_sendmsg(int fd,const struct msghdr *m,int flags) {
  if(m->msg_iovlen!=1 || m->msg_iov[0].iov_len<54)
    return __real_sendmsg(fd,m,flags);
  const unsigned char *original=m->msg_iov[0].iov_base;
  unsigned stage=original[9];
  if(getpid()!=factory && !is("rights_on_ready"))return __real_sendmsg(fd,m,flags);
  struct msghdr copy=*m;struct iovec io=*m->msg_iov;
  unsigned char data[1024];memcpy(data,original,io.iov_len);
  io.iov_base=data;copy.msg_iov=&io;
  if(stage==1 && is("replay_hello"))memset(data+14,0x42,40);
  if(stage==3 && m->msg_control)memcpy(&remembered_parent,CMSG_DATA(CMSG_FIRSTHDR(m)),sizeof(int));
  if((stage==5 && is("rights_on_commit")) ||
     (stage==2 && getpid()!=factory && is("rights_on_ready"))) {
    unsigned char ctl[CMSG_SPACE(sizeof(int))]={0};copy.msg_control=ctl;copy.msg_controllen=sizeof ctl;
    struct cmsghdr *h=CMSG_FIRSTHDR(&copy);h->cmsg_level=SOL_SOCKET;h->cmsg_type=SCM_RIGHTS;
    h->cmsg_len=CMSG_LEN(sizeof(int));int sent=stage==2?0:remembered_parent;
    memcpy(CMSG_DATA(h),&sent,sizeof sent);return __real_sendmsg(fd,&copy,flags);
  }
  if(stage==1 && is("send_error")){errno=EINTR;return -1;}
  if(stage==3 && !done_fault) {
    done_fault=1;
    if(is("nonce"))data[53]^=1;
    if(is("generation"))data[14]^=1;
    if(is("sequence"))data[13]^=1;
    if(is("stage"))data[9]=4;
    if(is("empty"))memset(data,0,4);
    if(is("oversize")){uint32_t n=htonl(513);memcpy(data,&n,4);}
    if(is("partial_prefix"))io.iov_len=2;
    if(is("partial_body"))io.iov_len=8;
    if(is("no_fd")){copy.msg_control=NULL;copy.msg_controllen=0;}
    unsigned char control[CMSG_SPACE(32*sizeof(int))];
    if(is("extra_fd") || is("truncated_fd") || is("wrong_type") ||
       is("wrong_dir") || is("fd_reuse")) {
      int sent;memcpy(&sent,CMSG_DATA(CMSG_FIRSTHDR(m)),sizeof sent);
      if(is("wrong_type") || is("fd_reuse"))foreign=open("/dev/null",O_RDONLY|O_CLOEXEC);
      if(is("wrong_dir")) {
        if(mkdir("foreign",0700))_exit(91);
        foreign=open("foreign",O_RDONLY|O_DIRECTORY|O_CLOEXEC);
      }
      if(is("fd_reuse")) {
        reused=sent;if(__real_close(sent) || dup2(foreign,sent)!=sent)_exit(92);
      } else if(foreign>=0)sent=foreign;
      int count=is("truncated_fd")?32:(is("extra_fd")?2:1);
      memset(control,0,sizeof control);copy.msg_control=control;
      copy.msg_controllen=CMSG_SPACE((size_t)count*sizeof(int));
      struct cmsghdr *h=CMSG_FIRSTHDR(&copy);h->cmsg_level=SOL_SOCKET;
      h->cmsg_type=SCM_RIGHTS;h->cmsg_len=CMSG_LEN((size_t)count*sizeof(int));
      for(int i=0;i<count;++i)memcpy((char *)CMSG_DATA(h)+i*sizeof(int),&sent,sizeof sent);
      return __real_sendmsg(fd,&copy,flags);
    }
    if(is("name_replaced")) {
      int sent;memcpy(&sent,CMSG_DATA(CMSG_FIRSTHDR(m)),sizeof sent);
      char path[128],old[4096],kept[4096];
      snprintf(path,sizeof path,"/proc/self/fd/%d",sent);
      ssize_t n=readlink(path,old,sizeof old-1);if(n<=0)_exit(93);old[n]=0;
      if(snprintf(kept,sizeof kept,"%s-kept",old)>=(int)sizeof kept ||
         rename(old,kept) || mkdir(old,0700))_exit(94);
    }
    if(is("duplicate_grant")) {
      if(__real_sendmsg(fd,&copy,flags)<0)return -1;
      return __real_sendmsg(fd,&copy,flags);
    }
    if(is("send_uncertain")) {
      if(__real_sendmsg(fd,&copy,flags)<0)return -1;
      errno=EINTR;return -1;
    }
  }
  if(stage==5) {
    if(is("omit_commit"))return (ssize_t)io.iov_len;
    if(is("extra_bytes")) {
      size_t n=io.iov_len;data[io.iov_len++]='x';
      ssize_t r=__real_sendmsg(fd,&copy,flags);return r==(ssize_t)(n+1)?(ssize_t)n:r;
    }
  }
  return __real_sendmsg(fd,&copy,flags);
}
ssize_t __wrap_recvmsg(int fd,struct msghdr *m,int flags) {
  ssize_t n=__real_recvmsg(fd,m,flags);
  if(n>=0)for(struct cmsghdr *h=CMSG_FIRSTHDR(m);h;h=CMSG_NXTHDR(m,h))
    if(h->cmsg_level==SOL_SOCKET && h->cmsg_type==SCM_RIGHTS)
      for(size_t i=0;i<(h->cmsg_len-CMSG_LEN(0))/sizeof(int);++i) {
        if(deliveries==128)__real__exit(97);
        memcpy(&delivered[deliveries],(char *)CMSG_DATA(h)+i*sizeof(int),sizeof(int));
        anchors[deliveries]=__real_fcntl(delivered[deliveries],F_DUPFD_CLOEXEC,80);
        if(anchors[deliveries]<0)__real__exit(97);
        consumed[deliveries++]=0;
      }
  if(getpid()==factory && n>=50 && !memcmp(m->msg_iov[0].iov_base,"NPG1",4) &&
     ((unsigned char *)m->msg_iov[0].iov_base)[5]==6)closed_seen=1;
  return n;
}
int __wrap_shutdown(int fd,int how) {
  if(getpid()==factory && is("missing_eof") && how==SHUT_WR)return 0;
  return __real_shutdown(fd,how);
}
int __wrap_close(int fd) {
  int tracking=0;
  for(int i=deliveries-1;i>=0;--i)if(delivered[i]==fd) {
    errno=0;int live=__real_fcntl(fd,F_GETFD);
    if((live<0 && errno==EBADF) || (live>=0 && same_ofd(fd,anchors[i]))) {
      ++consumed[i];tracking=1;break;
    }
    /* A new receive adds a new generation; a different OFD is not this delivery. */
  }
  struct stat st;int chosen=getpid()==factory && is("close_unknown") &&
    closed_seen && !fstat(fd,&st) && S_ISDIR(st.st_mode);
  if(getpid()==factory && is("base_close_unknown") && closed_seen && !fstat(fd,&st)) {
    struct stat base;
    if(!lstat("lab-fixtures",&base) && equal_object(&st,&base))chosen=1;
  }
  int r=__real_close(fd);
  if(!r && tracking && is("double_close_probe") && !double_injected) {
    double_injected=1;(void)__wrap_close(fd);
  }
  if(chosen && !close_faulted){close_faulted=1;errno=EINTR;return -1;}
  return r;
}
int __wrap_waitid(idtype_t type,id_t id,siginfo_t *info,int options) {
  if(getpid()==factory && is("wait_unknown")){errno=EINTR;return -1;}
  return __real_waitid(type,id,info,options);
}
int main(int argc,char **argv) {
  if(argc!=2)return 2;
  factory=getpid();fault=argv[1];
  int result=parent_handoff_fixed_main();check_received();
  if(foreign>=0) {
    if(fcntl(foreign,F_GETFD)<0)return 95;
    if(reused>=0 && fcntl(reused,F_GETFD)<0)return 96;
    if(reused>=0)__real_close(reused);
    __real_close(foreign);
  }
  return result;
}
