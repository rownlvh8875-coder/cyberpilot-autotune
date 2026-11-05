/* Unbound original-P / owned-D research successor. Credentials simulated only in tests. */
#pragma push_macro("main")
#undef main
#define main dr_old_entry_main
#include "../worker_entry/integration.c"
#undef main
#pragma pop_macro("main")
#include "internal.h"
static int dr_run_worker(int original_parent) {
  int image=-1,anchor=-1,ownerfd=-1,pidfd=-1,pipefd[2]={-1,-1},pair[2]={-1,-1};
  struct stat original={0};struct channel c={.fd=-1,.anchor=-1};struct frame f={0};
  int complete=0,born=0;struct dr_domain domain={.parent=-1,.parent_anchor=-1,.fd=-1,.anchor=-1};
  unsigned char ctx[CTX]={0},wire[CTX+4];
  struct ce_attempt pre=CE_ATTEMPT_INIT;
  if(now_ms()<0)return 40;
  if(entry_prebirth(&pre,&entry_ids)!=CE_SEALED_CREDENTIALS_ONLY)return 40;
  if(dr_create(&domain,original_parent))goto done;
  image=sealed_worker(&original);if(image<0)goto done;
  anchor=fcntl(image,F_DUPFD_CLOEXEC,3);
  ownerfd=(int)syscall(SYS_pidfd_open,getpid(),0u);
  if(!refs_match(image,anchor,&original) || ownerfd<0 ||
     pipe2(pipefd,O_CLOEXEC|O_NONBLOCK) ||
     socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0,pair))goto done;
  int one=1;
  if(setsockopt(pair[0],SOL_SOCKET,SO_PASSCRED,&one,sizeof one))goto done;
  struct clone_args args={0};args.flags=CLONE_PIDFD|CLONE_INTO_CGROUP;args.cgroup=(uint64_t)domain.fd;
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
  int64_t generation=now_ms();if(generation<0)goto done;
  memcpy(ctx,"NWE1\1\1",6);write64(ctx+10,(uint64_t)generation);
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
  if(dr_check(&domain,(int)child))goto done;
  if(send_stage(&c,ctx,3,2) || shutdown(c.fd,SHUT_WR) ||
     credential_frame(&c,&f,(pid_t)child,uid,gid) ||
     !check_frame(&f,ctx,4,3,CTX) || credential_end(&c,(pid_t)child,uid,gid))goto done;
  if(dr_check(&domain,(int)child) || dr_stop(&domain,(int)child) ||
     dr_wait_reclaim(&domain,&pidfd))goto done;
  complete=1;
done:
  channel_close(&c);close_one(&pair[0]);close_one(&pair[1]);
  close_one(&pipefd[0]);close_one(&pipefd[1]);
  if(pidfd>=0) {
    int owned=pidfd;pidfd=-1;
    if(!domain.stop_attempted && syscall(SYS_pidfd_send_signal,owned,SIGKILL,NULL,0))uncertain=1;
    struct pollfd waitfd={owned,POLLIN,0};siginfo_t info={0};
    if(poll(&waitfd,1,5500)!=1 || waitid(P_PIDFD,(id_t)owned,&info,WEXITED))uncertain=1;
    close_one(&owned);
  }
  if(dr_dispose(&domain))uncertain=1;
  close_one(&pidfd);close_one(&ownerfd);
  if(image>=0 || anchor>=0) {
    if(refs_match(image,anchor,&original)){close_one(&image);close_one(&anchor);}
    else uncertain=1;
  }
  return complete && !uncertain?0:(born?41:40);
}
static int dr_entry_peer(void) {
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
  int worker_result=dr_run_worker(parent);
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

int ci_peer_fixed(void) {
 pid_t manager=getppid();
 int null=open("/dev/null",O_RDWR|O_NOFOLLOW|O_CLOEXEC);
 if(manager<=1 || null<0 || dup2(null,1)!=1 || dup2(null,2)!=2 ||
    syscall(SYS_close_range,3u,~0u,0u) || getppid()!=manager)return 40;
 return dr_entry_peer();
}
