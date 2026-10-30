/* FIXED HARMLESS SOFTWARE GUEST ONLY. Never execute this ELF on the host. */
#define _GNU_SOURCE
#include "../../../../compatibility/guest_consumption/guest/sha256.h"
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <inttypes.h>
#include <limits.h>
#include <linux/audit.h>
#include <linux/kcmp.h>
#include <linux/ptrace.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define SCOPE "guest-data-fd-handoff-v1: fixed software guest only\n"
#define REQUIRED_SEALS 47
struct object { int rw,ro; struct stat st; char hash[65]; };
static struct object primary,alternate,program;
static uint64_t sequence;
static int generation,ready,denied,case_number,slot_epoch;
static int ofd[4]={-1,-1,-1,-1},ofd_error[4]={ENODATA,ENODATA,ENODATA,ENODATA};
static char output_buffer[65536];

static uint64_t mono(void)
{
  struct timespec t;if(clock_gettime(CLOCK_MONOTONIC,&t))_exit(2);
  return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;
}
static void event(const char *kind)
{
  if(++sequence>1024)_exit(2);
  printf("HFD [%"PRIu64",%"PRIu64",\"%s\"",sequence,mono(),kind);
}
static void end(void){puts("]");if(ferror(stdout))_exit(2);}
static long trace(unsigned request,pid_t tid,uintptr_t address,uintptr_t data)
{return syscall(SYS_ptrace,request,tid,address,data);}
static int same(const struct stat *a,const struct stat *b)
{
  return a->st_dev==b->st_dev&&a->st_ino==b->st_ino&&a->st_mode==b->st_mode&&
    a->st_size==b->st_size&&a->st_mtim.tv_sec==b->st_mtim.tv_sec&&
    a->st_mtim.tv_nsec==b->st_mtim.tv_nsec&&a->st_ctim.tv_sec==b->st_ctim.tv_sec&&
    a->st_ctim.tv_nsec==b->st_ctim.tv_nsec;
}
static int hash_fd(int fd,struct stat *st,char hash[65])
{
  if(fstat(fd,st)||!S_ISREG(st->st_mode)||st->st_size<0||st->st_size>4*1024*1024)return -1;
  struct sha256_ctx ctx;sha256_init(&ctx);unsigned char bytes[4096];off_t at=0;
  for(;;){ssize_t n=pread(fd,bytes,sizeof(bytes),at);if(n<0)return -1;if(!n)break;
    at+=n;if(at>4*1024*1024)return -1;sha256_update(&ctx,bytes,(size_t)n);}
  struct stat after;if(fstat(fd,&after)||at!=st->st_size||!same(st,&after))return -1;
  sha256_final(&ctx,hash);return 0;
}
static void identity(const struct stat *st,const char *hash)
{printf(",%"PRIu64",%"PRIu64",%"PRIu64",\"%s\"",
  (uint64_t)st->st_dev,(uint64_t)st->st_ino,(uint64_t)st->st_size,hash);}
static int seals(int fd,int *error)
{errno=0;int value=fcntl(fd,F_GET_SEALS);*error=value<0?errno:0;return value;}
static void nullable(int value){if(value<0)printf(",null");else printf(",%d",value);}
static int object(const char *label,struct object *o,int empty)
{
  o->rw=-1;o->ro=-1;
  if(!strcmp(label,"program"))o->ro=open("/data-fd-handoff-probe",O_RDONLY|O_CLOEXEC);
  else{
    /* MFD_NOEXEC_SEAL=8: match PR32 DATA mode, no executable/default fallback. */
    o->rw=memfd_create("fixed-data-only",MFD_CLOEXEC|MFD_ALLOW_SEALING|8);if(o->rw<0)return -1;
    const char bytes[]="fixed DATA bytes\n";
    if(!empty&&write(o->rw,bytes,sizeof(bytes)-1)!=(ssize_t)(sizeof(bytes)-1))return -1;
    if(fcntl(o->rw,F_ADD_SEALS,REQUIRED_SEALS))return -1;
    char path[80];snprintf(path,sizeof(path),"/proc/self/fd/%d",o->rw);
    o->ro=open(path,O_RDONLY|O_CLOEXEC);
  }
  if(o->ro<0||hash_fd(o->ro,&o->st,o->hash))return -1;
  int error,value=seals(o->ro,&error);
  event("OBJECT");printf(",\"%s\"",label);identity(&o->st,o->hash);nullable(value);
  printf(",%d",error);end();return 0;
}
static int count_directory(const char *path)
{
  DIR *dir=opendir(path);if(!dir)return -1;int count=0;struct dirent *entry;
  errno=0;while((entry=readdir(dir))){if(!strcmp(entry->d_name,".")||!strcmp(entry->d_name,".."))continue;
    if(++count>64){closedir(dir);return -1;}}
  int error=errno;if(closedir(dir)||error)return -1;return count;
}
static int target_flags(pid_t child,int fd,unsigned long *flags)
{
  char path[96],line[256];snprintf(path,sizeof(path),"/proc/%d/fdinfo/%d",child,fd);
  FILE *f=fopen(path,"re");if(!f)return -1;int found=0;
  while(fgets(line,sizeof(line),f))if(sscanf(line,"flags:\t%lo",flags)==1)found++;
  int error=ferror(f);if(fclose(f)||error||found!=1)return -1;return 0;
}
static int fd_observation(pid_t child,const char *stage,int fd,struct object *expected,int wanted_cloexec)
{
  char path[96];snprintf(path,sizeof(path),"/proc/%d/fd/%d",child,fd);
  int held=open(path,O_RDONLY|O_CLOEXEC|O_NONBLOCK);if(held<0)return -1;
  struct stat st;char hash[65];unsigned long flags;
  if(hash_fd(held,&st,hash)||target_flags(child,fd,&flags)){close(held);return -1;}
  int error,value=seals(held,&error);close(held);
  int comparison=-1,compare_error=ENODATA;
  if(fd<4){
    compare_error=ofd_error[fd];
    if(ofd[fd]>=0){errno=0;comparison=(int)syscall(SYS_kcmp,getpid(),child,KCMP_FILE,ofd[fd],fd);
      compare_error=comparison<0?errno:0;}
  }
  event("FD");printf(",\"%s\",%d,%d,%d,%"PRIu64",%"PRIu64",%"PRIu64",%lu",
    stage,generation,fd,fd==0?slot_epoch:0,(uint64_t)st.st_dev,(uint64_t)st.st_ino,
    (uint64_t)st.st_size,flags);nullable(value);printf(",%d,\"%s\"",error,hash);
  nullable(comparison);printf(",%d",compare_error);end();
  return same(&st,&expected->st)&&!strcmp(hash,expected->hash)&&value==REQUIRED_SEALS&&
    (flags&O_ACCMODE)==O_RDONLY&&!!(flags&O_CLOEXEC)==wanted_cloexec?0:1;
}
static int credentials(pid_t child,int *uid,int *gid,int *nnp)
{
  char path[96],line[256];snprintf(path,sizeof(path),"/proc/%d/status",child);
  FILE *f=fopen(path,"re");if(!f)return -1;unsigned a,b,c,d;int found=0;
  while(fgets(line,sizeof(line),f)){
    if(sscanf(line,"Uid:\t%u\t%u\t%u\t%u",&a,&b,&c,&d)==4){if(a!=b||b!=c||c!=d){fclose(f);return -1;}*uid=(int)a;found++;}
    if(sscanf(line,"Gid:\t%u\t%u\t%u\t%u",&a,&b,&c,&d)==4){if(a!=b||b!=c||c!=d){fclose(f);return -1;}*gid=(int)a;found++;}
    if(sscanf(line,"NoNewPrivs:\t%d",nnp)==1)found++;
  }
  int error=ferror(f);if(fclose(f)||error||found!=3)return -1;return 0;
}
static int snapshot(pid_t child,const char *stage)
{
  char path[96];snprintf(path,sizeof(path),"/proc/%d/fd",child);
  DIR *dir=opendir(path);if(!dir)return -1;int fds[64],count=0;struct dirent *entry;
  errno=0;while((entry=readdir(dir))){
    if(!strcmp(entry->d_name,".")||!strcmp(entry->d_name,".."))continue;
    char *tail=NULL;long number=strtol(entry->d_name,&tail,10);
    if(!tail||*tail||number<0||number>INT_MAX||count==64){closedir(dir);return -1;}
    fds[count++]=(int)number;
  }
  int error=errno;if(closedir(dir)||error)return -1;
  for(int i=0;i<count;i++)for(int j=i+1;j<count;j++)if(fds[j]<fds[i]){int x=fds[i];fds[i]=fds[j];fds[j]=x;}
  int binding=0;
  for(int i=0;i<count;i++){
    struct object *wanted=&primary;if(case_number==2||(!strcmp(stage,"REUSED")&&fds[i]==0)||
      (case_number==6&&fds[i]==3))wanted=&alternate;
    int cloexec=(strcmp(stage,"PRE_EXEC")||case_number==5)&&!(!strcmp(stage,"REUSED")&&fds[i]==0);
    int result=fd_observation(child,stage,fds[i],wanted,cloexec);
    if(result<0)return -1;
    binding|=result;
    /* HH02 intentionally expects primary: equal bytes are not its object identity. */
    if(case_number==2&&same(&wanted->st,&alternate.st))binding=1;
  }
  int uid=-1,gid=-1,nnp=-1;
  snprintf(path,sizeof(path),"/proc/%d/task",child);int threads=count_directory(path);
  if(threads<0||credentials(child,&uid,&gid,&nnp))return -1;
  event("SNAP");printf(",\"%s\",%d,%d,%d,%d,%d,%d,null",stage,generation,count,threads,uid,gid,nnp);end();
  int bootstrap=!strcmp(stage,"PRE_TRANSFER");
  if(threads!=1||uid!=(bootstrap?0:65534)||gid!=(bootstrap?0:65534)||nnp!=(bootstrap?0:1))return -1;
  if(!strcmp(stage,"PRE_TRANSFER")||!strcmp(stage,"CLOSED"))return count?1:0;
  int wanted_count=case_number==6?2:1;
  if(count!=wanted_count)return 1;
  if(fds[0]!=0||(wanted_count==2&&fds[1]!=3))return 1;
  return binding;
}
static void deny(pid_t child,const char *reason)
{
  if(!denied){event("DENY");printf(",\"%s\",%d,0",reason,generation);end();}
  denied=1;kill(child,SIGKILL);
}
static int memory(pid_t child,uint64_t address,unsigned char *out,size_t n)
{
  for(size_t at=0;at<n;){uintptr_t current=(uintptr_t)address+at,aligned=current&~(sizeof(long)-1);
    long word=0;if(trace(PTRACE_PEEKDATA,child,aligned,(uintptr_t)&word)<0)return -1;
    size_t skip=current-aligned,take=sizeof(long)-skip;if(take>n-at)take=n-at;
    memcpy(out+at,(unsigned char *)&word+skip,take);at+=take;}
  return 0;
}
static int guest_guard(int parent)
{
  struct utsname u;if(uname(&u)||strcmp(u.release,"6.12.113+deb13-cloud-amd64")||
    strcmp(u.machine,"x86_64")||geteuid()!=(parent?0:65534))return -1;
  if(!parent)return 0; /* Payload guard opens no file and creates no extra capability. */
  int fd=open("/etc/data-fd-handoff-scope",O_RDONLY|O_CLOEXEC);if(fd<0)return -1;
  char bytes[128];ssize_t n=read(fd,bytes,sizeof(bytes));close(fd);
  return n==(ssize_t)strlen(SCOPE)&&!memcmp(bytes,SCOPE,(size_t)n)?0:-1;
}
static int payload(void)
{
  if(guest_guard(0))return 2;
  unsigned char bytes[17];
  if(case_number==4){pread(0,bytes,sizeof(bytes),0);return 2;}
  if(fcntl(0,F_SETFD,FD_CLOEXEC)<0&&case_number!=5)return 2;
  if(case_number==6&&fcntl(3,F_SETFD,FD_CLOEXEC)<0)return 2;
  raise(SIGSTOP);
  if(case_number==6){if(close(0)||dup2(3,0)!=0)return 2;}
  ssize_t n=pread(0,bytes,sizeof(bytes),0);
  if(n!=(case_number==7?0:17)||close(0))return 2;
  if(case_number==6)close(3);
  return 0;
}
static void bootstrap(pid_t parent,const char *selected)
{
  int first=case_number==2?alternate.ro:primary.ro;
  int second=case_number==6?alternate.ro:primary.ro;
  if(syscall(SYS_close_range,0,UINT_MAX,0)||trace(PTRACE_TRACEME,0,0,0)<0)_exit(2);
  raise(SIGSTOP); /* Supervisor observes actual empty descriptor table. */
  char path[96];snprintf(path,sizeof(path),"/proc/%d/fd/%d",parent,first);
  int opened=open(path,O_RDONLY|O_CLOEXEC);if(opened<0)_exit(2);
  if(opened!=0){if(dup2(opened,0)<0)_exit(2);close(opened);}
  if(fcntl(0,F_SETFD,case_number==5?FD_CLOEXEC:0)<0)_exit(2);
  if(case_number==3||case_number==6){
    snprintf(path,sizeof(path),"/proc/%d/fd/%d",parent,second);
    opened=open(path,O_RDONLY|O_CLOEXEC);if(opened<0)_exit(2);
    if(opened!=3){if(dup2(opened,3)<0)_exit(2);close(opened);}
    if(fcntl(3,F_SETFD,0)<0)_exit(2);
  }
  if(setgroups(0,NULL)||setgid(65534)||setuid(65534)||prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))_exit(2);
  raise(SIGSTOP); /* Actual installed, still pre-exec; credentials already dropped. */
  execl("/data-fd-handoff-probe","data-fd-handoff-probe","--payload",selected,(char *)NULL);_exit(2);
}
static void pin_ofd(pid_t child,int fd)
{
  errno=0;int pidfd=(int)syscall(SYS_pidfd_open,child,0),result=-1,error;
  if(pidfd<0)error=errno;
  else{errno=0;result=(int)syscall(SYS_pidfd_getfd,pidfd,fd,0);error=result<0?errno:0;close(pidfd);}
  ofd[fd]=result;ofd_error[fd]=error;
  event("OFD_PIN");printf(",%d,%d,%d",fd,result,error);end();
}
static void release(const char *label,int fd)
{event("RELEASE");printf(",\"%s\",%d",label,close(fd));end();}
static int collect(const char *selected)
{
  if(guest_guard(1)||sha256_selfcheck())return 2;
  setvbuf(stdout,output_buffer,_IOLBF,sizeof(output_buffer));
  event("BEGIN");printf(",\"guest-data-fd-handoff-observed-v1\",\"%s\",\"GUEST_MONOTONIC_NS\"",selected);end();
  if(object("primary",&primary,case_number==7)||object("program",&program,0))return 2;
  if((case_number==2||case_number==6)&&object("alternate",&alternate,0))return 2;
  pid_t parent=getpid(),child=fork();if(child<0)return 2;if(!child)bootstrap(parent,selected);
  int status;if(waitpid(child,&status,0)!=child||!WIFSTOPPED(status)||WSTOPSIG(status)!=SIGSTOP)return 2;
  if(trace(PTRACE_SETOPTIONS,child,0,PTRACE_O_TRACESYSGOOD|PTRACE_O_TRACEEXEC|PTRACE_O_EXITKILL)<0)return 2;
  event("BIRTH");printf(",1");end();
  if(snapshot(child,"PRE_TRANSFER"))return 2;
  int stops=0,pending=0;uint64_t nr=0,args[6]={0};
  if(trace(PTRACE_SYSCALL,child,0,0)<0)return 2;
  for(;;){
    if(waitpid(child,&status,__WALL)!=child)return 2;
    if(WIFEXITED(status)||WIFSIGNALED(status)){
      event("REAP");printf(",%d,\"%s\",%d",generation,WIFEXITED(status)?"EXITED":"SIGNALLED",
        WIFEXITED(status)?WEXITSTATUS(status):WTERMSIG(status));end();break;
    }
    if(!WIFSTOPPED(status))return 2;
    unsigned ptrace_event=(unsigned)status>>16;int sig=WSTOPSIG(status);
    if(denied){kill(child,SIGKILL);trace(PTRACE_SYSCALL,child,0,SIGKILL);continue;}
    if(ptrace_event==PTRACE_EVENT_EXEC){
      char path[96],hash[65];struct stat st;snprintf(path,sizeof(path),"/proc/%d/exe",child);
      int fd=open(path,O_RDONLY|O_CLOEXEC);if(fd<0||hash_fd(fd,&st,hash))return 2;close(fd);
      generation++;event("EXEC");printf(",0,%d",generation);identity(&st,hash);end();
      if(generation!=1||!same(&st,&program.st)||strcmp(hash,program.hash))return 2;
    }else if(sig==SIGSTOP){
      stops++;
      if(stops==1){
        int check=snapshot(child,"PRE_EXEC");if(check<0)return 2;
        if(case_number==2)deny(child,"PRE_EXEC_BINDING");
        else if(case_number==3)deny(child,"EXTRA_FD");
        else if(check)return 2;
        else{pin_ofd(child,0);if(case_number==6)pin_ofd(child,3);}
        /* HH05 deliberately injects CLOEXEC loss, never normal-policy admission. */
      }else if(stops==2&&generation==1){
        int check=snapshot(child,"POST_EXEC");if(check<0)return 2;
        if(check)deny(child,"POST_EXEC_BINDING");
        else{ready=1;event("READY");printf(",1");end();}
      }else return 2;
    }else if(sig==(SIGTRAP|0x80)){
      struct ptrace_syscall_info info;memset(&info,0,sizeof(info));
      if(trace(PTRACE_GET_SYSCALL_INFO,child,sizeof(info),(uintptr_t)&info)<0||info.arch!=AUDIT_ARCH_X86_64)return 2;
      if(info.op==PTRACE_SYSCALL_INFO_ENTRY){
        nr=info.entry.nr;memcpy(args,info.entry.args,sizeof(args));pending=1;
        if(nr==SYS_fork||nr==SYS_vfork||nr==SYS_clone||nr==SYS_clone3||
           (nr==SYS_execve&&generation)){deny(child,"UNSUPPORTED_TASK_OR_EXEC");}
        if(generation&&(nr==SYS_read||nr==SYS_pread64)){
          if(!ready)deny(child,"EARLY_READ");
          else if(slot_epoch)deny(child,"BINDING_CHANGED");
          else if(nr!=SYS_pread64||args[0]!=0||args[2]!=17||args[3]!=0||
                  fd_observation(child,"READ_CHECK",0,&primary,1))return 2;
        }
      }else if(info.op==PTRACE_SYSCALL_INFO_EXIT){
        if(!pending)return 2;
        pending=0;int64_t result=info.exit.rval;
        if(generation&&nr==SYS_pread64){
          if(result<0||result>17)return 2;
          unsigned char bytes[17];if(memory(child,args[1],bytes,(size_t)result))return 2;
          event("READ");printf(",1,0,%d,0,17,%"PRId64",\"",slot_epoch,result);
          for(int64_t i=0;i<result;i++)printf("%02x",bytes[i]);
          printf("\"");end();
        }else if(generation&&ready&&nr==SYS_close&&args[0]==0){
          event("CLOSE");printf(",1,0,%d,%"PRId64,slot_epoch,result);end();
          if(result)return 2;
          if(case_number!=6&&snapshot(child,"CLOSED"))return 2;
        }else if(generation&&ready&&nr==SYS_dup2){
          if(case_number!=6||slot_epoch||args[0]!=3||args[1]!=0||result!=0)return 2;
          slot_epoch=1;event("DUP");printf(",1,3,0,1,%"PRId64,result);end();
          /* Explicit predeclared negative injection, not supported rebind behavior. */
          if(snapshot(child,"REUSED"))return 2;
        }
      }else return 2;
    }else return 2;
    if(trace(PTRACE_SYSCALL,child,0,denied?SIGKILL:0)<0&&errno!=ESRCH)return 2;
  }
  release("primary_rw",primary.rw);release("primary_ro",primary.ro);release("program",program.ro);
  if(case_number==2||case_number==6){release("alternate_rw",alternate.rw);release("alternate_ro",alternate.ro);}
  for(int fd=0;fd<4;fd++)if(ofd[fd]>=0){char label[16];snprintf(label,sizeof(label),"ofd_%d",fd);release(label,ofd[fd]);}
  event("END");printf(",%d,null",generation);end();return fflush(stdout)||ferror(stdout)?2:0;
}
int main(int argc,char **argv)
{
  if(argc!=3||strlen(argv[2])!=4||memcmp(argv[2],"HH0",3)||argv[2][3]<'1'||argv[2][3]>'7')return 2;
  case_number=argv[2][3]-'0';
  if(!strcmp(argv[1],"--trace"))return collect(argv[2]);
  if(!strcmp(argv[1],"--payload"))return payload();
  return 2;
}
