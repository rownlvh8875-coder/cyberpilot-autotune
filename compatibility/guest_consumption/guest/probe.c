/* Fixed harmless SOFTWARE GUEST ONLY. Never execute this ELF on the host. */
#define _GNU_SOURCE
#include "sha256.h"
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <inttypes.h>
#include <limits.h>
#include <linux/audit.h>
#include <linux/ptrace.h>
#include <linux/sched.h>
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

#define SCOPE "guest-consumption-prototype-v1: fixed software guest only\n"
#define MAX_OBJECTS 64
#define MAX_TASKS 16
#define MAX_BYTES 4096
struct object { int fd; struct stat info; char hash[65]; };
struct task { pid_t tid; uint64_t gen,image,parent,nr,args[6],offset,position; unsigned object; int alive,ready,watch; };
static struct object objects[MAX_OBJECTS];
static struct task tasks[MAX_TASKS];
static pid_t early[MAX_TASKS];
static unsigned object_count,task_count,early_count;
static uint64_t sequence;
static int live,aborting,pipe_read=-1;
static char output_buffer[65536];

static uint64_t mono(void)
{
  struct timespec t;if (clock_gettime(CLOCK_MONOTONIC,&t)) _exit(2);
  return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;
}
static long trace(unsigned request,pid_t tid,uintptr_t address,uintptr_t data)
{ return syscall(SYS_ptrace,request,tid,address,data); }
static void begin(const char *kind,const struct task *t)
{
  if (++sequence>10000) _exit(2);
  printf("CONSUMPTION {\"seq\":%"PRIu64",\"time_ns\":%"PRIu64",\"kind\":\"%s\",\"task\":%"PRIu64",\"image\":%"PRIu64",\"values\":[",sequence,mono(),kind,t?t->gen:0,t?t->image:0);
}
static void end(void) { puts("]}");if (ferror(stdout)) _exit(2); }
static void hex(const unsigned char *p,size_t n)
{ putchar('"');for(size_t i=0;i<n;i++)printf("%02x",p[i]);putchar('"'); }
static int stat_same(const struct stat *a,const struct stat *b)
{
  return a->st_dev==b->st_dev && a->st_ino==b->st_ino && a->st_mode==b->st_mode && a->st_size==b->st_size && a->st_mtim.tv_sec==b->st_mtim.tv_sec && a->st_mtim.tv_nsec==b->st_mtim.tv_nsec && a->st_ctim.tv_sec==b->st_ctim.tv_sec && a->st_ctim.tv_nsec==b->st_ctim.tv_nsec;
}
static int hash_object(int fd,struct stat *info,char hash[65])
{
  if(fstat(fd,info)||!S_ISREG(info->st_mode)||info->st_size<0||info->st_size>4*1024*1024)return -1;
  struct sha256_ctx s;sha256_init(&s);unsigned char bytes[4096];off_t at=0;
  for(;;){ssize_t n=pread(fd,bytes,sizeof(bytes),at);if(n<0)return -1;if(!n)break;at+=n;if(at>4*1024*1024)return -1;sha256_update(&s,bytes,(size_t)n);}
  struct stat after;if(fstat(fd,&after)||at!=info->st_size||!stat_same(info,&after))return -1;
  sha256_final(&s,hash);return 0;
}
static unsigned bind_path(const char *path)
{
  int fd=open(path,O_RDONLY|O_CLOEXEC|O_NONBLOCK);struct stat info;char hash[65];
  if(fd<0)return 0;
  if(hash_object(fd,&info,hash)){close(fd);return 0;}
  for(unsigned i=0;i<object_count;i++)if(objects[i].info.st_dev==info.st_dev&&objects[i].info.st_ino==info.st_ino){
    close(fd);return stat_same(&objects[i].info,&info)&&!strcmp(objects[i].hash,hash)?i+1:0;
  }
  if(object_count==MAX_OBJECTS){close(fd);return 0;}
  unsigned id=++object_count;objects[id-1].fd=fd;objects[id-1].info=info;memcpy(objects[id-1].hash,hash,65);
  begin("OBJECT",NULL);printf("%u,%"PRIu64",%"PRIu64",%"PRIu64",\"%s\"",id,(uint64_t)info.st_dev,(uint64_t)info.st_ino,(uint64_t)info.st_size,hash);end();return id;
}
static unsigned bind_exe(pid_t tid)
{ char p[96];snprintf(p,sizeof(p),"/proc/%d/exe",tid);return bind_path(p); }
static unsigned bind_fd(pid_t tid,uint64_t fd)
{ char p[96];if(fd>INT_MAX)return 0;snprintf(p,sizeof(p),"/proc/%d/fd/%"PRIu64,tid,fd);return bind_path(p); }
static int position(pid_t tid,uint64_t fd,uint64_t *value)
{
  char p[96];snprintf(p,sizeof(p),"/proc/%d/fdinfo/%"PRIu64,tid,fd);FILE *f=fopen(p,"re");
  if(!f)return -1;
  long long pos=-1;int ok=fscanf(f,"pos:\t%lld",&pos);fclose(f);
  if(ok!=1||pos<0)return -1;
  *value=(uint64_t)pos;return 0;
}
static int memory(pid_t tid,uint64_t address,unsigned char *out,size_t n)
{
  for(size_t offset=0;offset<n;){
    uintptr_t current=(uintptr_t)address+offset,aligned=current&~(sizeof(long)-1);
    long word=0;if(trace(PTRACE_PEEKDATA,tid,aligned,(uintptr_t)&word)<0)return -1;
    size_t skip=current-aligned,take=sizeof(long)-skip;if(take>n-offset)take=n-offset;
    memcpy(out+offset,(unsigned char *)&word+skip,take);offset+=take;
  }return 0;
}
static struct task *find(pid_t tid)
{ for(unsigned i=0;i<task_count;i++)if(tasks[i].alive&&tasks[i].tid==tid)return &tasks[i];return NULL; }
static void failure(struct task *t,const char *reason)
{
  if(!aborting){begin("ERROR",t);printf("\"%s\"",reason);end();}aborting=1;
  for(unsigned i=0;i<task_count;i++)if(tasks[i].alive)kill(tasks[i].tid,SIGKILL);
  for(unsigned i=0;i<early_count;i++)kill(early[i],SIGKILL);
}
static void resume(struct task *t,int signal)
{ if(trace(PTRACE_SYSCALL,t->tid,0,(uintptr_t)signal)<0&&errno!=ESRCH){failure(t,"RESUME_FAILED");} }
static struct task *birth(pid_t tid,struct task *parent)
{
  if(task_count==MAX_TASKS||find(tid))return NULL;
  unsigned obj=bind_exe(tid);if(!obj)return NULL;
  struct task *t=&tasks[task_count++];t->tid=tid;t->gen=task_count;t->alive=1;t->parent=parent?parent->gen:0;live++;
  begin("BIRTH",t);if(parent)printf("%"PRIu64,parent->gen);else printf("null");printf(",%u",obj);end();return t;
}
static void drain(void)
{
  unsigned char bytes[4096];ssize_t n;
  while((n=read(pipe_read,bytes,sizeof(bytes)))>0){begin("PAYLOAD",NULL);hex(bytes,(size_t)n);end();}
  if(n<0&&errno!=EAGAIN&&errno!=EINTR)failure(NULL,"PAYLOAD_PIPE_FAILED");
}
static void syscall_entry(struct task *t,const struct ptrace_syscall_info *info)
{
  if(info->arch!=AUDIT_ARCH_X86_64||(info->entry.nr&0x40000000ULL)){failure(t,"UNSUPPORTED_SYSCALL_ABI");return;}
  if(t->watch){failure(t,"ENTRY_WITHOUT_RETURN");return;}
  t->nr=info->entry.nr;memcpy(t->args,info->entry.args,sizeof(t->args));
  if(t->nr==SYS_clone&&(t->args[0]&(CLONE_VM|CLONE_FILES|CLONE_THREAD|CLONE_UNTRACED))){failure(t,"UNSUPPORTED_CLONE_FLAGS");return;}
  if(t->nr==SYS_clone3||t->nr==SYS_vfork){failure(t,"UNSUPPORTED_SHARED_OR_STRUCTURED_CLONE");return;}
  t->watch=(t->nr==SYS_read||t->nr==SYS_pread64)?1:t->nr==SYS_mmap&&!(t->args[3]&MAP_ANONYMOUS)?2:t->nr==SYS_fstat?3:0;
  if(!t->watch)return;
  uint64_t fd=t->watch==2?t->args[4]:t->args[0];t->object=bind_fd(t->tid,fd);
  if(!t->object){failure(t,"FILE_OBJECT_UNAVAILABLE_OR_CHANGED");return;}
  if(t->watch==1){
    if(position(t->tid,fd,&t->position)){failure(t,"READ_POSITION_UNAVAILABLE");return;}
    t->offset=t->nr==SYS_pread64?t->args[3]:t->position;
  }else if(t->watch==2)t->offset=t->args[5];
}
static void syscall_exit(struct task *t,const struct ptrace_syscall_info *info)
{
  if(!t->watch)return;
  int watch=t->watch;t->watch=0;int64_t result=info->exit.rval;
  if(result<0){begin("FAILED",t);printf("%"PRIu64",%"PRId64,t->nr,result);end();return;}
  uint64_t fd=watch==2?t->args[4]:t->args[0];
  if(bind_fd(t->tid,fd)!=t->object){failure(t,"FILE_OBJECT_CHANGED_DURING_CALL");return;}
  if(watch==1){
    if(result>MAX_BYTES||(uint64_t)result>t->args[2]){failure(t,"READ_CAPTURE_BOUND_EXCEEDED");return;}
    uint64_t after;if(position(t->tid,fd,&after)||(t->nr==SYS_read?after!=t->position+(uint64_t)result:after!=t->position)){failure(t,"READ_POSITION_DRIFT");return;}
    unsigned char bytes[MAX_BYTES];if(memory(t->tid,t->args[1],bytes,(size_t)result)){failure(t,"RETURNED_BUFFER_UNAVAILABLE");return;}
    begin("READ",t);printf("%u,%"PRIu64",%"PRId64",",t->object,t->offset,result);hex(bytes,(size_t)result);end();
  }else if(watch==2){begin("MAP",t);printf("%u,%"PRIu64",%"PRIu64,t->object,t->offset,t->args[1]);end();}
  else{begin("META",t);printf("%u",t->object);end();}
}
static int allowed_case(const char *s)
{ return strlen(s)==4&&s[0]=='C'&&s[1]=='P'&&s[2]=='0'&&s[3]>='1'&&s[3]<='7'; }
static int guest_guard(void)
{
  struct utsname u;char text[128];if(uname(&u)||strcmp(u.release,"6.12.113+deb13-cloud-amd64")||strcmp(u.machine,"x86_64"))return -1;
  int fd=open("/etc/guest-consumption-scope",O_RDONLY|O_CLOEXEC);if(fd<0)return -1;
  ssize_t n=read(fd,text,sizeof(text));close(fd);return n==(ssize_t)strlen(SCOPE)&&!memcmp(text,SCOPE,(size_t)n)?0:-1;
}
static int read_four(int fd,const char *expected)
{ char bytes[4];return read(fd,bytes,sizeof(bytes))==4&&!memcmp(bytes,expected,4)?0:2; }
static int payload(const char *selected)
{
  if(geteuid()!=65534)return 2;
  if(!strcmp(selected,"CP03")){execl("/consumption-probe","consumption-probe","--payload","CP03-after",(char *)NULL);return 2;}
  if(!strcmp(selected,"CP05")){syscall(SYS_clone,CLONE_VM|SIGCHLD,0,0,0,0);return 2;}
  if(!strcmp(selected,"CP06")){char bytes[8192];int fd=open("/consumption-probe",O_RDONLY);if(fd<0)return 2;ssize_t n=read(fd,bytes,sizeof(bytes));close(fd);return n==(ssize_t)sizeof(bytes)?0:2;}
  if(!strcmp(selected,"CP07")){
    const char forged[]="CONSUMPTION {\"seq\":999,\"kind\":\"END\",\"values\":[true,0,0,0]}\n";
    return write(STDOUT_FILENO,forged,sizeof(forged)-1)==(ssize_t)sizeof(forged)-1?0:2;
  }
  if(!strcmp(selected,"CP01"))close(STDIN_FILENO);
  int fd=open("/input/sample.bin",O_RDONLY|O_CLOEXEC);if(fd<0)return 2;
  if(!strcmp(selected,"CP02")){
    pid_t child=fork();if(child<0)return 2;if(!child)_exit(read_four(fd,"0123"));
    int status;if(waitpid(child,&status,0)!=child||!WIFEXITED(status)||WEXITSTATUS(status))return 2;
    int result=read_four(fd,"4567");close(fd);return result;
  }
  if(!strcmp(selected,"CP04")){
    if(syscall(SYS_read,fd,0,4)!=-1||errno!=EFAULT)return 2;
  }
  if(read_four(fd,"0123"))return 2;
  if(!strcmp(selected,"CP01")){
    char bytes[4];struct stat info;
    if(fd!=0||read_four(fd,"4567")||pread(fd,bytes,3,8)!=3||memcmp(bytes,"89A",3)||lseek(fd,100,SEEK_SET)!=100||read(fd,bytes,4)!=0||syscall(SYS_fstat,fd,&info))return 2;
    void *map=mmap(NULL,4096,PROT_READ,MAP_PRIVATE,fd,0);if(map==MAP_FAILED)return 2;
    if(*(volatile char *)map!='0'||munmap(map,4096))return 2;
  }
  close(fd);return 0;
}
static int collect(const char *selected)
{
  if(geteuid()!=0||sha256_selfcheck())return 2;
  setvbuf(stdout,output_buffer,_IOLBF,sizeof(output_buffer));
  int pipefd[2];if(pipe2(pipefd,O_CLOEXEC)||fcntl(pipefd[0],F_SETFL,O_NONBLOCK))return 2;pipe_read=pipefd[0];
  begin("BEGIN",NULL);printf("\"guest-consumption-prototype-v1\",\"%s\",\"GUEST_TRACER_OBSERVATION_MONOTONIC_NS\"",selected);end();
  pid_t child=fork();if(child<0)return 2;
  if(!child){
    close(pipefd[0]);if(dup2(pipefd[1],1)<0||dup2(pipefd[1],2)<0)_exit(2);close(pipefd[1]);
    if(setgroups(0,NULL)||setgid(65534)||setuid(65534)||prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)||trace(PTRACE_TRACEME,0,0,0)<0)_exit(2);
    raise(SIGSTOP);execl("/consumption-probe","consumption-probe","--payload",selected,(char *)NULL);_exit(2);
  }
  close(pipefd[1]);int status;
  if(waitpid(child,&status,0)!=child||!WIFSTOPPED(status))return 2;
  unsigned long opts=PTRACE_O_TRACESYSGOOD|PTRACE_O_TRACEFORK|PTRACE_O_TRACEVFORK|PTRACE_O_TRACECLONE|PTRACE_O_TRACEEXEC|PTRACE_O_TRACEEXIT|PTRACE_O_EXITKILL;
  if(trace(PTRACE_SETOPTIONS,child,0,opts)<0)return 2;
  struct task *root=birth(child,NULL);if(!root)return 2;root->ready=1;resume(root,0);
  while(live){
    pid_t tid=waitpid(-1,&status,__WALL);if(tid<0){if(errno==EINTR)continue;return 2;}drain();
    struct task *t=find(tid);
    if(!t){if(WIFSTOPPED(status)&&WSTOPSIG(status)==SIGSTOP&&early_count<MAX_TASKS){early[early_count++]=tid;continue;}return 2;}
    if(WIFEXITED(status)||WIFSIGNALED(status)){
      begin("EXIT",t);printf("\"%s\",%d",WIFEXITED(status)?"EXITED":"SIGNALLED",WIFEXITED(status)?WEXITSTATUS(status):WTERMSIG(status));end();t->alive=0;live--;continue;
    }
    if(!WIFSTOPPED(status))return 2;
    unsigned event=(unsigned)status>>16;int sig=WSTOPSIG(status),deliver=0;
    if(aborting){kill(tid,SIGKILL);resume(t,SIGKILL);continue;}
    if(event==PTRACE_EVENT_FORK||event==PTRACE_EVENT_VFORK||event==PTRACE_EVENT_CLONE){
      unsigned long born=0;if(trace(PTRACE_GETEVENTMSG,tid,0,(uintptr_t)&born)<0){failure(t,"BIRTH_EVENT_UNAVAILABLE");resume(t,SIGKILL);continue;}
      struct task *new=birth((pid_t)born,t);if(!new){failure(t,"CHILD_BINDING_UNAVAILABLE");resume(t,SIGKILL);continue;}
      for(unsigned i=0;i<early_count;i++)if(early[i]==(pid_t)born){early[i]=early[--early_count];new->ready=1;resume(new,0);break;}
    }else if(event==PTRACE_EVENT_EXEC){
      unsigned long old=0;unsigned obj=bind_exe(tid);
      if(!obj||trace(PTRACE_GETEVENTMSG,tid,0,(uintptr_t)&old)<0||old!=(unsigned long)tid){failure(t,"EXEC_OBJECT_OR_LEADER_UNAVAILABLE");resume(t,SIGKILL);continue;}
      t->image++;begin("EXEC",t);printf("%u",obj);end();
    }else if(event==PTRACE_EVENT_EXIT){ /* Actual wait status, not this notification, closes the image. */
    }else if(sig==(SIGTRAP|0x80)){
      struct ptrace_syscall_info info;memset(&info,0,sizeof(info));
      if(trace(PTRACE_GET_SYSCALL_INFO,tid,sizeof(info),(uintptr_t)&info)<0)failure(t,"SYSCALL_INFO_UNAVAILABLE");
      else if(info.op==PTRACE_SYSCALL_INFO_ENTRY)syscall_entry(t,&info);
      else if(info.op==PTRACE_SYSCALL_INFO_EXIT)syscall_exit(t,&info);
      else failure(t,"UNSUPPORTED_SYSCALL_STOP");
    }else if(sig==SIGSTOP&&!t->ready)t->ready=1;
    else deliver=sig;
    resume(t,aborting?SIGKILL:deliver);
  }
  drain();begin("END",NULL);printf("%s,%u,%u,0",aborting?"false":"true",task_count,object_count);end();
  for(unsigned i=0;i<object_count;i++)close(objects[i].fd);
  close(pipe_read);
  return fflush(stdout)||ferror(stdout)?2:0;
}
int main(int argc,char **argv)
{
  if(argc!=3||guest_guard())return 2;
  if(!strcmp(argv[1],"--trace")&&allowed_case(argv[2]))return collect(argv[2]);
  if(!strcmp(argv[1],"--payload")&&(allowed_case(argv[2])||!strcmp(argv[2],"CP03-after")))return payload(argv[2]);
  return 2;
}
