/* Unbound fixed same-UID research integration. No production/provider entry. */
#pragma push_macro("main")
#undef main
#define main parent_handoff_reference_main
#include "../parent_handoff/handoff.c"
#undef main
#pragma pop_macro("main")
#include "entry_credential.h"
#include <elf.h>
#include <linux/memfd.h>
#include <sys/sysmacros.h>
#ifndef ENTRY_CREDENTIAL_BOUNDARY
#define ENTRY_CREDENTIAL_BOUNDARY "LIVE_PREFLIGHT_REJECTED"
#endif
static const struct ce_ids entry_ids={17001,17002,18001,18002};
static int alive(int fd) {
  struct pollfd p={fd,POLLIN,0};
  return poll(&p,1,0)==0;
}
static uint32_t get32(const unsigned char *b) {
  uint32_t v;memcpy(&v,b,4);return ntohl(v);
}
static void put32(unsigned char *b,uint32_t v) {v=htonl(v);memcpy(b,&v,4);}
/* Fixed adjacent compiled worker only. No external filename or executable API.
 * A sealed memfd protects retained bytes after copy, not their source authenticity.
 * Trusted private build directory assumption; no protected factory/F1 claim. */
static int sealed_worker(struct stat *identity) {
  int source=-1,image=-1,folder=-1,ok=0;char self[4096];struct stat st;
  ssize_t n=readlink("/proc/self/exe",self,sizeof self-1);
  if(n<=0 || n>=(ssize_t)sizeof self-1)goto done;
  self[n]=0;char *slash=strrchr(self,'/');if(!slash)goto done;*slash=0;
  folder=open(self,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
  if(folder<0 || fstat(folder,&st) || st.st_uid!=geteuid() || (st.st_mode&0022))goto done;
  source=openat(folder,"fixed-worker",O_RDONLY|O_NOFOLLOW|O_CLOEXEC);
  if(source<0 || fstat(source,&st) || !S_ISREG(st.st_mode) || st.st_uid!=geteuid() ||
     (st.st_mode&06022) || !(st.st_mode&S_IXUSR) || st.st_size<64 || st.st_size>131072)goto done;
  unsigned char bytes[131072];size_t used=0;
  while(used<(size_t)st.st_size) {
    ssize_t r=read(source,bytes+used,(size_t)st.st_size-used);
    if(r<=0)goto done;
    used+=(size_t)r;
  }
  unsigned char extra;if(read(source,&extra,1)!=0)goto done;
  Elf64_Ehdr header;memcpy(&header,bytes,sizeof header);
  if(memcmp(header.e_ident,ELFMAG,SELFMAG) || header.e_ident[EI_CLASS]!=ELFCLASS64 ||
     header.e_ident[EI_DATA]!=ELFDATA2LSB || header.e_machine!=EM_X86_64 ||
     header.e_type!=ET_EXEC || header.e_phentsize!=sizeof(Elf64_Phdr) ||
     header.e_phnum>32 || header.e_phoff>used ||
     header.e_phnum*sizeof(Elf64_Phdr)>used-header.e_phoff)goto done;
  for(unsigned i=0;i<header.e_phnum;++i) {
    Elf64_Phdr ph;memcpy(&ph,bytes+header.e_phoff+i*sizeof ph,sizeof ph);
    if(ph.p_type==PT_INTERP)goto done;
  }
  image=(int)syscall(SYS_memfd_create,"fixed-synthetic-worker",MFD_CLOEXEC|MFD_ALLOW_SEALING);
  if(image<0 || write(image,bytes,used)!=(ssize_t)used ||
     fcntl(image,F_ADD_SEALS,F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL) ||
     fcntl(image,F_GET_SEALS)!=(F_SEAL_WRITE|F_SEAL_GROW|F_SEAL_SHRINK|F_SEAL_SEAL) ||
     fstat(image,identity))goto done;
  ok=1;
done:
  close_one(&source);close_one(&folder);
  if(!ok || uncertain)close_one(&image);
  return image;
}
/* Every nonempty recv chunk must carry kernel sender credentials. SO_PEERCRED
 * is deliberately not used: a pre-birth socketpair stamps the creator, not W. */
static ssize_t credential_receive(struct channel *c,void *out,size_t size,
                                  pid_t child,uid_t uid,gid_t gid) {
  if(now_ms()<0 || ready(c,POLLIN))return -1;
  union {struct cmsghdr align;unsigned char b[CMSG_SPACE(sizeof(struct ucred))+
    CMSG_SPACE(RIGHTS*sizeof(int))];} control;
  struct iovec io={out,size};struct msghdr m={0};
  m.msg_iov=&io;m.msg_iovlen=1;m.msg_control=control.b;m.msg_controllen=sizeof control;
  ssize_t n=recvmsg(c->fd,&m,MSG_CMSG_CLOEXEC|MSG_DONTWAIT);
  if(n<0)return -1;
  unsigned count=0;int bad=(m.msg_flags&(MSG_CTRUNC|MSG_TRUNC))!=0;
  for(struct cmsghdr *h=CMSG_FIRSTHDR(&m);h;h=CMSG_NXTHDR(&m,h)) {
    if(h->cmsg_level==SOL_SOCKET && h->cmsg_type==SCM_CREDENTIALS &&
       h->cmsg_len==CMSG_LEN(sizeof(struct ucred))) {
      struct ucred cred;memcpy(&cred,CMSG_DATA(h),sizeof cred);++count;
      if(n>0) {if(cred.pid!=child || cred.uid!=uid || cred.gid!=gid)bad=1;}
      else if(cred.pid || cred.uid || cred.gid)bad=1;
    } else {
      bad=1;
      if(h->cmsg_level==SOL_SOCKET && h->cmsg_type==SCM_RIGHTS && h->cmsg_len>=CMSG_LEN(0)) {
        size_t bytes=h->cmsg_len-CMSG_LEN(0);
        for(size_t i=0;i<bytes/sizeof(int);++i) {
          int fd;memcpy(&fd,(char *)CMSG_DATA(h)+i*sizeof fd,sizeof fd);close_one(&fd);
        }
      }
    }
  }
  /* Linux stream EOF may include one zero-valued synthetic credential.
   * It is NOT sender evidence; a zero-length framed message still rejects. */
  if((n>0 && count!=1) || count>1)bad=1;
  return bad?-1:n;
}
static int credential_exact(struct channel *c,void *out,size_t size,pid_t pid,uid_t uid,gid_t gid) {
  size_t used=0;
  while(used<size) {
    ssize_t n=credential_receive(c,(char *)out+used,size-used,pid,uid,gid);
    if(n<=0)return -1;
    used+=(size_t)n;
  }
  return 0;
}
static int credential_frame(struct channel *c,struct frame *f,pid_t pid,uid_t uid,gid_t gid) {
  uint32_t size;memset(f,0,sizeof *f);
  if(credential_exact(c,&size,4,pid,uid,gid))return -1;
  f->len=ntohl(size);
  if(!f->len || f->len>MAX_FRAME)return -1;
  return credential_exact(c,f->data,f->len,pid,uid,gid);
}
static int credential_end(struct channel *c,pid_t pid,uid_t uid,gid_t gid) {
  unsigned char b;return credential_receive(c,&b,1,pid,uid,gid)==0?0:-1;
}
static int exec_eof(int fd,int64_t deadline) {
  int64_t current=now_ms();if(current<0)return -1;
  int64_t left=deadline-current;
  if(left<=0 || left>2500)return -1;
  struct pollfd p={fd,POLLIN,0};unsigned char error;
  return poll(&p,1,(int)left)==1 && read(fd,&error,1)==0?0:-1;
}
static void worker_birth(int endpoint,int image,int errorfd,int ownerfd,pid_t owner) {
  int a=fcntl(endpoint,F_DUPFD_CLOEXEC,32),b=fcntl(image,F_DUPFD_CLOEXEC,32);
  int d=fcntl(errorfd,F_DUPFD_CLOEXEC,32),o=fcntl(ownerfd,F_DUPFD_CLOEXEC,32);
  struct pollfd p={ownerfd,POLLIN,0};
  if(a<0 || b<0 || d<0 || o<0 || poll(&p,1,0)!=0 || getppid()!=owner)_exit(71);
  int null=open("/dev/null",O_RDWR|O_NOFOLLOW|O_CLOEXEC);struct stat st;
  if(null<0 || fstat(null,&st) || !S_ISCHR(st.st_mode) || st.st_rdev!=makedev(1,3))_exit(71);
  for(int i=0;i<3;++i)if(dup2(null,i)!=i)_exit(71);
  if(dup3(a,3,0)!=3 || dup3(b,4,O_CLOEXEC)!=4 || dup3(d,5,O_CLOEXEC)!=5 ||
     dup3(o,6,O_CLOEXEC)!=6 || syscall(SYS_close_range,7u,~0u,0u))_exit(71);
  struct ce_attempt seal=CE_ATTEMPT_INIT;
  if(ce_seal_worker(&seal,&entry_ids)!=CE_SEALED_CREDENTIALS_ONLY)goto failed;
  /* Recheck ORIGINAL parent after seal; no cross-UID proc/ptrace lookup.
   * Close this last parent-control handle before entering the fixed ELF. */
  p.fd=6;p.revents=0;
  if(poll(&p,1,0)!=0 || getppid()!=owner || close(6))goto failed;
  char *const args[]={"fixed-synthetic-worker",NULL};
  char *const env[]={"LANG=C",NULL};
  /* Empty-path exec of original sealed FD; no pathname fallback. */
  syscall(SYS_execveat,4,"",args,env,AT_EMPTY_PATH);
failed:
  {const unsigned char e=1;if(write(5,&e,1)!=1)_exit(72);}
  _exit(71);
}
static int run_worker(void) {
  int image=-1,anchor=-1,ownerfd=-1,pidfd=-1,pipefd[2]={-1,-1},pair[2]={-1,-1};
  struct stat original={0};struct channel c={.fd=-1,.anchor=-1};struct frame f={0};
  int complete=0,exitcode=-1,born=0;
  unsigned char ctx[CTX]={0},wire[CTX+4];
  struct ce_attempt pre=CE_ATTEMPT_INIT;
  if(now_ms()<0)return 40;
  if(entry_prebirth(&pre,&entry_ids)!=CE_SEALED_CREDENTIALS_ONLY)return 40;
  image=sealed_worker(&original);if(image<0)goto done;
  anchor=fcntl(image,F_DUPFD_CLOEXEC,3);
  ownerfd=(int)syscall(SYS_pidfd_open,getpid(),0u);
  if(!refs_match(image,anchor,&original) || ownerfd<0 ||
     pipe2(pipefd,O_CLOEXEC|O_NONBLOCK) ||
     socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0,pair))goto done;
  int one=1;
  if(setsockopt(pair[0],SOL_SOCKET,SO_PASSCRED,&one,sizeof one))goto done;
  struct clone_args args={0};args.flags=CLONE_PIDFD;
  args.pidfd=(uint64_t)(uintptr_t)&pidfd;args.exit_signal=SIGCHLD;
  pid_t owner=getpid();uid_t uid=getuid();gid_t gid=getgid();
  long child=syscall(SYS_clone3,&args,sizeof args);
  born=pidfd>=0; /* creation handle survives a cancelled/ambiguous return */
  if(child<0)goto done;
  if(!child)worker_birth(pair[1],image,pipefd[1],ownerfd,owner);
  born=1;
  close_one(&pair[1]);close_one(&pipefd[1]);
  struct ce_attempt seal=CE_ATTEMPT_INIT;
  if(ce_seal_owner(&seal,&entry_ids)!=CE_SEALED_CREDENTIALS_ONLY)goto done;
  int endpoint=pair[0];pair[0]=-1;
  if(channel_init(&c,endpoint) || exec_eof(pipefd[0],c.deadline) || !alive(pidfd))goto done;
  memcpy(ctx,"NWE1\1\1",6);write64(ctx+10,(uint64_t)now_ms());
  if(getrandom(ctx+18,32,0)!=32)goto done;
  message(wire,ctx,1,0);put32(wire+CTX,(uint32_t)owner);
  if(send_frame(&c,wire,sizeof wire,-1) ||
     credential_frame(&c,&f,(pid_t)child,uid,gid) ||
     !check_frame(&f,ctx,2,1,CTX+32) || !alive(pidfd) ||
     !refs_match(image,anchor,&original) ||
     read64(f.data+CTX)!=(uint64_t)original.st_dev ||
     read64(f.data+CTX+8)!=(uint64_t)original.st_ino ||
     get32(f.data+CTX+16)!=(uint32_t)owner ||
     get32(f.data+CTX+20)!=uid || get32(f.data+CTX+24)!=gid ||
     get32(f.data+CTX+28)!=15)goto done;
  if(send_stage(&c,ctx,3,2) || shutdown(c.fd,SHUT_WR) ||
     credential_frame(&c,&f,(pid_t)child,uid,gid) ||
     !check_frame(&f,ctx,4,3,CTX) || credential_end(&c,(pid_t)child,uid,gid))goto done;
  complete=1;
done:
  channel_close(&c);close_one(&pair[0]);close_one(&pair[1]);
  close_one(&pipefd[0]);close_one(&pipefd[1]);
  if(pidfd>=0 && reap_original(pidfd,&exitcode))uncertain=1;
  close_one(&pidfd);close_one(&ownerfd);
  if(image>=0 || anchor>=0) {
    if(refs_match(image,anchor,&original)){close_one(&image);close_one(&anchor);}
    else uncertain=1;
  }
  return complete && exitcode==0 && !uncertain?0:(born?41:40);
}
static int entry_peer(void) {
  struct channel c={.fd=-1,.anchor=-1};struct frame f={0};
  int parent=-1,anchor=-1,accepted=0,result=40;struct stat original={0};
  unsigned char ctx[CTX];
  if(channel_init(&c,0) || read_frame(&c,&f,0) || f.len!=CTX ||
     memcmp(f.data,"NPG1\1\1\0\0\0\0",10))goto done;
  memcpy(ctx,f.data,CTX);
  if(send_stage(&c,ctx,2,1) || read_frame(&c,&f,1))goto done;
  if(!check_frame(&f,ctx,3,2,CTX+16) || f.nfds!=1)goto done;
  struct stat st;int flags=fcntl(f.fds[0],F_GETFD);
  if(flags<0 || !(flags&FD_CLOEXEC) || fstat(f.fds[0],&st) || !S_ISDIR(st.st_mode) ||
     (uint64_t)st.st_dev!=read64(f.data+CTX) ||
     (uint64_t)st.st_ino!=read64(f.data+CTX+8))goto done;
  parent=f.fds[0];f.fds[0]=-1;f.nfds=0;original=st;
  anchor=fcntl(parent,F_DUPFD_CLOEXEC,3);
  if(!refs_match(parent,anchor,&original) || send_stage(&c,ctx,4,3) ||
     read_frame(&c,&f,0) || !check_frame(&f,ctx,5,4,CTX) || end_of_stream(&c))goto done;
  /* Hold original private P across fixed W proof; no systemd/cgroup claim. */
  int worker_result=run_worker();
  /* Birth is monotonic observation: a later P/channel failure cannot erase it. */
  result=worker_result==0?41:worker_result;
  if(worker_result || !refs_match(parent,anchor,&original))goto done;
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
  return accepted && !uncertain?0:(result==41?41:40);
}
static int await_entry_peer(struct channel *c) {
  /* Outer F must outlive W's protocol timeout + E's original-child wait.
   * This bounded wait does not retry or reconstruct any process handle. */
  if(!channel_ok(c))return -1;
  struct pollfd p={c->fd,POLLIN,0};
  if(poll(&p,1,6500)!=1)return -1;
  c->deadline=now_ms()+2500;return 0;
}
int main(void) {
  uncertain=0;
  int pair[2]={-1,-1},basefd=-1,parent=-1,anchor=-1,pidfd=-1,exit_code=-1,complete=0,removed=0;
  struct channel c={.fd=-1,.anchor=-1};struct stat original={0};
  char leaf[48]="parent-";unsigned char name_random[16];
  unsigned char ctx[CTX]={0},wire[CTX+16];struct frame f={0};
  if(geteuid()==0 || now_ms()<0)goto done;
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
    _exit(entry_peer());
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
     send_stage(&c,ctx,5,4) || shutdown(c.fd,SHUT_WR) || await_entry_peer(&c) ||
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
  int success=complete && exit_code==0 && removed && !uncertain && now_ms()>=0;
  char peer_status[24];
  if(exit_code<0)strcpy(peer_status,"null");
  else snprintf(peer_status,sizeof peer_status,"%d",exit_code);
  printf("{\"outcome\":\"%s\",\"cleanup\":\"%s\",\"peer_exit\":%s,"
    "\"parent_removed\":%s,\"cgroup_authority\":false,\"credential_kernel_verified\":false,"
    "\"credential_boundary\":\"%s\",\"worker_started\":%s,",
    success?"FIXED_ENTRY_FIXTURE_COMPLETE":"REJECTED",success?"CONFIRMED":"UNKNOWN",
    peer_status,removed?"true":"false",ENTRY_CREDENTIAL_BOUNDARY,
    exit_code==0 || exit_code==41?"true":(exit_code==40?"false":"null"));
  const char *fact=success?"true":"null";
  printf("\"original_exec\":%s,\"fd_entry\":%s,\"parent_relation\":%s,\"kernel_sender\":%s}\n",
    fact,fact,fact,fact);
  return success?0:20;
}
