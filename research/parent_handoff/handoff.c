#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <linux/kcmp.h>
#include <linux/magic.h>
#include <linux/sched.h>
#include <poll.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#if !defined(__x86_64__) || defined(__ILP32__) || __SIZEOF_POINTER__ != 8 || \
    __SIZEOF_LONG__ != 8 || __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "Parent handoff fixture requires Linux x86_64 LP64 little endian"
#endif

/* Fixed, nonprivileged regular-directory fixture. NOT a systemd/cgroup provider.
 * No pathname/PID/FD/command input, no payload/RUN stage, no receipt recovery. */
#define CTX 50
#define MAX_FRAME 512
#define RIGHTS 8
static int uncertain;
struct channel {int fd,anchor;struct stat original;int64_t deadline;};
struct frame {unsigned char data[MAX_FRAME];size_t len;int fds[RIGHTS];size_t nfds;};
static int64_t now_ms(void) {
  struct timespec t;
  if(clock_gettime(CLOCK_MONOTONIC,&t))return -1;
  return (int64_t)t.tv_sec*1000+t.tv_nsec/1000000;
}
static void close_one(int *fd) {
  if(*fd<0)return;
  int original=*fd;*fd=-1;
  if(close(original))uncertain=1; /* consumed once, never retry EINTR */
}
static int equal_object(const struct stat *a,const struct stat *b) {
  return a->st_dev==b->st_dev && a->st_ino==b->st_ino &&
    (a->st_mode&S_IFMT)==(b->st_mode&S_IFMT);
}
static int same_ofd(int a,int b) {
  return syscall(SYS_kcmp,getpid(),getpid(),KCMP_FILE,(unsigned long)a,(unsigned long)b)==0;
}
static int refs_match(int a,int b,const struct stat *original) {
  struct stat x,y;
  return a>=0 && b>=0 && !fstat(a,&x) && !fstat(b,&y) &&
    equal_object(&x,original) && equal_object(&y,original) && same_ofd(a,b);
}
static int channel_init(struct channel *c,int fd) {
  c->fd=fd;c->anchor=-1;c->deadline=now_ms()+2500;
  int type=0,domain=0;socklen_t n=sizeof type;
  if(fstat(fd,&c->original) || !S_ISSOCK(c->original.st_mode) ||
     getsockopt(fd,SOL_SOCKET,SO_TYPE,&type,&n) || type!=SOCK_STREAM)return -1;
  n=sizeof domain;
  if(getsockopt(fd,SOL_SOCKET,SO_DOMAIN,&domain,&n) || domain!=AF_UNIX)return -1;
  c->anchor=fcntl(fd,F_DUPFD_CLOEXEC,3);
  return c->anchor<0?-1:0;
}
static int channel_ok(struct channel *c) {
  if(!refs_match(c->fd,c->anchor,&c->original)){uncertain=1;return 0;}
  return 1;
}
static void channel_close(struct channel *c) {
  if(c->fd<0 && c->anchor<0)return;
  if(!channel_ok(c))return; /* foreign/reused numbers must not be closed */
  close_one(&c->fd);close_one(&c->anchor);
}
static int ready(struct channel *c,short events) {
  int64_t remaining=c->deadline-now_ms();
  if(!channel_ok(c) || remaining<=0 || remaining>2500)return -1;
  struct pollfd p={c->fd,events,0};
  return poll(&p,1,(int)remaining)==1?0:-1;
}
static void frame_clear(struct frame *f) {
  for(size_t i=0;i<f->nfds;++i)close_one(&f->fds[i]);
  f->nfds=0;
}
static ssize_t receive(struct channel *c,void *out,size_t size,struct frame *f) {
  if(ready(c,POLLIN))return -1;
  union {struct cmsghdr alignment;unsigned char data[CMSG_SPACE(RIGHTS*sizeof(int))];} control;
  struct iovec io={out,size};
  struct msghdr m={0};m.msg_iov=&io;m.msg_iovlen=1;
  m.msg_control=control.data;m.msg_controllen=sizeof control.data;
  ssize_t n=recvmsg(c->fd,&m,MSG_CMSG_CLOEXEC|MSG_DONTWAIT);
  if(n<0)return -1;
  int bad=(m.msg_flags&(MSG_CTRUNC|MSG_TRUNC))!=0;
  for(struct cmsghdr *h=CMSG_FIRSTHDR(&m);h;h=CMSG_NXTHDR(&m,h)) {
    if(h->cmsg_len<CMSG_LEN(0) || h->cmsg_level!=SOL_SOCKET || h->cmsg_type!=SCM_RIGHTS) {
      bad=1;continue;
    }
    size_t bytes=h->cmsg_len-CMSG_LEN(0);
    if(bytes%sizeof(int))bad=1;
    for(size_t i=0;i<bytes/sizeof(int);++i) {
      int fd;memcpy(&fd,(char *)CMSG_DATA(h)+i*sizeof(int),sizeof fd);
      if(f->nfds<RIGHTS)f->fds[f->nfds++]=fd;
      else {close_one(&fd);bad=1;}
    }
  }
  return bad?-1:n;
}
static int exact_read(struct channel *c,void *out,size_t size,struct frame *f) {
  size_t used=0;
  while(used<size) {
    ssize_t n=receive(c,(char *)out+used,size-used,f);
    if(n<=0)return -1;
    used+=(size_t)n;
  }
  return 0;
}
static int read_frame(struct channel *c,struct frame *f,int rights_allowed) {
  memset(f,0,sizeof *f);uint32_t size;
  if(exact_read(c,&size,4,f))goto bad;
  f->len=ntohl(size);
  if(!f->len || f->len>MAX_FRAME || exact_read(c,f->data,f->len,f))goto bad;
  if(f->nfds && !rights_allowed)goto bad;
  return 0;
bad:
  frame_clear(f);return -1;
}
static int end_of_stream(struct channel *c) {
  struct frame f={0};unsigned char extra;
  ssize_t n=receive(c,&extra,1,&f);
  int ok=n==0 && f.nfds==0;
  frame_clear(&f);return ok?0:-1;
}
static uint64_t read64(const void *p) {
  uint64_t value;memcpy(&value,p,8);return be64toh(value);
}
static void write64(void *p,uint64_t value) {value=htobe64(value);memcpy(p,&value,8);}
static void message(unsigned char *out,const unsigned char *ctx,unsigned stage,unsigned seq) {
  memcpy(out,ctx,CTX);out[5]=(unsigned char)stage;
  uint32_t sequence=htonl(seq);memcpy(out+6,&sequence,4);
}
static int check_frame(struct frame *f,const unsigned char *ctx,unsigned stage,unsigned seq,size_t length) {
  unsigned char expected[CTX];message(expected,ctx,stage,seq);
  return f->len==length && !memcmp(f->data,expected,CTX);
}
static int send_frame(struct channel *c,const unsigned char *data,size_t size,int grant) {
  if(!size || size>MAX_FRAME || ready(c,POLLOUT))return -1;
  unsigned char packet[MAX_FRAME+4];uint32_t n=htonl((uint32_t)size);
  memcpy(packet,&n,4);memcpy(packet+4,data,size);
  struct iovec io={packet,size+4};struct msghdr m={0};
  m.msg_iov=&io;m.msg_iovlen=1;
  union {struct cmsghdr alignment;unsigned char data[CMSG_SPACE(sizeof(int))];} control;
  if(grant>=0) {
    memset(&control,0,sizeof control);m.msg_control=control.data;m.msg_controllen=sizeof control;
    struct cmsghdr *h=CMSG_FIRSTHDR(&m);h->cmsg_level=SOL_SOCKET;
    h->cmsg_type=SCM_RIGHTS;h->cmsg_len=CMSG_LEN(sizeof(int));
    memcpy(CMSG_DATA(h),&grant,sizeof grant);
  }
  /* A short/error send may already have transferred rights. Never resend. */
  return sendmsg(c->fd,&m,MSG_NOSIGNAL|MSG_DONTWAIT)==(ssize_t)(size+4)?0:-1;
}
static int send_stage(struct channel *c,const unsigned char *ctx,unsigned stage,unsigned seq) {
  unsigned char data[CTX];message(data,ctx,stage,seq);return send_frame(c,data,CTX,-1);
}
static int peer(void) {
  struct channel c={.fd=-1,.anchor=-1};struct frame f={0};
  int parent=-1,anchor=-1,accepted=0;struct stat original={0};
  unsigned char ctx[CTX];
  if(channel_init(&c,0) || read_frame(&c,&f,0) || f.len!=CTX ||
     memcmp(f.data,"NPG1\1\1\0\0\0\0",10))goto done;
  memcpy(ctx,f.data,CTX);
  if(send_stage(&c,ctx,2,1) || read_frame(&c,&f,1))goto done;
  if(!check_frame(&f,ctx,3,2,CTX+16) || f.nfds!=1)goto done;
  struct stat st;int descriptor_flags=fcntl(f.fds[0],F_GETFD);
  if(descriptor_flags<0 || fstat(f.fds[0],&st) || !S_ISDIR(st.st_mode) ||
     (uint64_t)st.st_dev!=read64(f.data+CTX) ||
     (uint64_t)st.st_ino!=read64(f.data+CTX+8) ||
     !(descriptor_flags&FD_CLOEXEC))goto done;
  parent=f.fds[0];f.fds[0]=-1;f.nfds=0;original=st;
  anchor=fcntl(parent,F_DUPFD_CLOEXEC,3);
  if(!refs_match(parent,anchor,&original) || send_stage(&c,ctx,4,3) ||
     read_frame(&c,&f,0) || !check_frame(&f,ctx,5,4,CTX) || end_of_stream(&c))goto done;
  if(!refs_match(parent,anchor,&original)) {uncertain=1;goto done;}
  close_one(&parent);close_one(&anchor);
  if(uncertain || send_stage(&c,ctx,6,5) || shutdown(c.fd,SHUT_WR))goto done;
  accepted=1;
done:
  frame_clear(&f);
  if(parent>=0 || anchor>=0) {
    if(refs_match(parent,anchor,&original)){close_one(&parent);close_one(&anchor);}
    else uncertain=1;
  }
  channel_close(&c);
  return accepted && !uncertain?0:20;
}
static int parent_original(int fd,int anchor,const struct stat *expected,int base,const char *leaf) {
  struct stat name;
  return refs_match(fd,anchor,expected) && !fstatat(base,leaf,&name,AT_SYMLINK_NOFOLLOW) &&
    S_ISDIR(name.st_mode) && equal_object(&name,expected);
}
static int reap_original(int pidfd,int *exit_code) {
  struct pollfd p={pidfd,POLLIN,0};
  if(poll(&p,1,1500)!=1) {
    if(syscall(SYS_pidfd_send_signal,pidfd,SIGKILL,NULL,0))uncertain=1;
    if(poll(&p,1,1000)!=1)return -1;
  }
  siginfo_t info={0};
  /* Exactly one wait, never reconstruct PID from a receipt or path. */
  if(waitid(P_PIDFD,(id_t)pidfd,&info,WEXITED))return -1;
  if(info.si_code==CLD_EXITED)*exit_code=info.si_status;
  else if(info.si_code==CLD_KILLED)*exit_code=128+info.si_status;
  else return -1;
  return 0;
}
int main(void) {
  uncertain=0;
  int pair[2]={-1,-1},basefd=-1,parent=-1,anchor=-1,pidfd=-1,exit_code=-1,complete=0,removed=0;
  struct channel c={.fd=-1,.anchor=-1};struct stat original={0};
  char leaf[48]="parent-";unsigned char name_random[16];
  unsigned char ctx[CTX]={0},wire[CTX+16];struct frame f={0};
  if(geteuid()==0)goto done;
  struct stat base;struct statfs fs;
  basefd=open("lab-fixtures",O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);
  if(basefd<0 || fstat(basefd,&base) || !S_ISDIR(base.st_mode) ||
     base.st_uid!=geteuid() || (base.st_mode&0077) || fstatfs(basefd,&fs) ||
     ((unsigned long)fs.f_type==CGROUP_SUPER_MAGIC ||
      (unsigned long)fs.f_type==CGROUP2_SUPER_MAGIC))goto done;
  if(getrandom(name_random,sizeof name_random,0)!=(ssize_t)sizeof name_random)goto done;
  for(size_t i=0;i<sizeof name_random;++i)
    snprintf(leaf+7+i*2,3,"%02x",name_random[i]);
  if(mkdirat(basefd,leaf,0700))goto done; /* one exclusive creation, no adoption/retry */
  parent=openat(basefd,leaf,O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);
  if(parent<0 || fstat(parent,&original))goto done;
  anchor=fcntl(parent,F_DUPFD_CLOEXEC,3);
  if(!parent_original(parent,anchor,&original,basefd,leaf) ||
     socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0,pair))goto done;
  struct clone_args args={0};args.flags=CLONE_PIDFD;
  args.pidfd=(uint64_t)(uintptr_t)&pidfd;args.exit_signal=SIGCHLD;
  long child=syscall(SYS_clone3,&args,sizeof args);
  if(child<0)goto done;
  if(!child) {
    if(dup2(pair[1],0)!=0 || syscall(SYS_close_range,3u,~0u,0u))_exit(20);
    _exit(peer());
  }
  close_one(&pair[1]);
  int endpoint=pair[0];pair[0]=-1;
  if(channel_init(&c,endpoint))goto done;
  memcpy(ctx,"NPG1\1\1",6);write64(ctx+10,(uint64_t)now_ms());
  if(getrandom(ctx+18,32,0)!=32 || uncertain || send_stage(&c,ctx,1,0) ||
     read_frame(&c,&f,0) || !check_frame(&f,ctx,2,1,CTX) ||
     !parent_original(parent,anchor,&original,basefd,leaf))goto done;
  message(wire,ctx,3,2);write64(wire+CTX,(uint64_t)original.st_dev);
  write64(wire+CTX+8,(uint64_t)original.st_ino);
  if(send_frame(&c,wire,sizeof wire,parent) || read_frame(&c,&f,0) ||
     !check_frame(&f,ctx,4,3,CTX) || !parent_original(parent,anchor,&original,basefd,leaf) ||
     send_stage(&c,ctx,5,4) || shutdown(c.fd,SHUT_WR) ||
     read_frame(&c,&f,0) || !check_frame(&f,ctx,6,5,CTX) || end_of_stream(&c))goto done;
  complete=1;
done:
  frame_clear(&f);
  channel_close(&c);close_one(&pair[0]);close_one(&pair[1]);
  if(pidfd>=0 && reap_original(pidfd,&exit_code))uncertain=1;
  close_one(&pidfd);
  if(parent>=0 || anchor>=0) {
    if(parent_original(parent,anchor,&original,basefd,leaf)) {
      close_one(&parent);close_one(&anchor);
      if(complete && exit_code==0 && !uncertain) {
        if(unlinkat(basefd,leaf,AT_REMOVEDIR))uncertain=1;else removed=1;
      }
    } else uncertain=1; /* retain unknown mapping; no foreign close/name cleanup */
  }
  /* Removal is an observed fact. A later base-handle close may be UNKNOWN:
   * report parent_removed=true + cleanup=UNKNOWN; never recreate or retry. */
  close_one(&basefd);
  int success=complete && exit_code==0 && removed && !uncertain;
  printf("{\"outcome\":\"%s\",\"cleanup\":\"%s\",\"peer_exit\":",
    success?"PARENT_HANDOFF_FIXTURE_COMPLETE":"REJECTED",success?"CONFIRMED":"UNKNOWN");
  if(exit_code<0)printf("null");else printf("%d",exit_code);
  printf(",\"parent_removed\":%s,\"cgroup_authority\":false,\"worker_started\":false}\n",
    removed?"true":"false");
  return success?0:20;
}
