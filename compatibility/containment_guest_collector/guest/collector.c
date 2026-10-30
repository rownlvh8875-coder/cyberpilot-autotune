/* Fixed harmless software guest ONLY. Never run this binary on the outer host. */
#define _GNU_SOURCE
#include "collector.h"
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <linux/audit.h>
#include <linux/ptrace.h>
#include <linux/sched.h>
#include <linux/seccomp.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define MAX_TASKS 64
#define MAX_EVENTS 1000000
struct task {
  pid_t tid;
  uint64_t generation, image, call, nr, args[6], clone_flags;
  int alive, ready, seed, pending, ioctl_kind;
  struct seccomp_notif_addfd add;
  struct seccomp_notif_resp reply;
  struct fd_record fds[COLLECTOR_MAX_FDS];
  int fd_count;
};
static struct task tasks[MAX_TASKS];
static uint64_t task_count, sequence, call_count;
static int live, first_value, output_pipe=-1;
static char output_line[8192];
static size_t output_size;
/* An automatically stopped child may reach waitpid before its parent's FORK
 * event (kernel wakes the child first). Hold it; never invent birth from PID. */
static pid_t early_stops[MAX_TASKS];
static int early_count;

static long trace(unsigned int request, pid_t tid, uintptr_t address, uintptr_t data)
{ return syscall(SYS_ptrace,request,tid,address,data); }

static uint64_t monotonic_ns(void)
{
  struct timespec now;
  if (clock_gettime(CLOCK_MONOTONIC,&now)) _exit(2);
  return (uint64_t)now.tv_sec*1000000000ULL+(uint64_t)now.tv_nsec;
}
static void begin_event(const char *kind, const struct task *task)
{
  if (++sequence>MAX_EVENTS) _exit(2);
  printf("TRACE_EVENT {\"kind\":\"%s\",\"seq\":%" PRIu64 ",\"mono_ns\":%" PRIu64
         ",\"task\":%" PRIu64 ",\"tid\":%d,\"image\":%" PRIu64 ",\"values\":[",
         kind,sequence,monotonic_ns(),task->generation,task->tid,task->image);
  first_value=1;
}
static void number(uint64_t value)
{ printf("%s%" PRIu64,first_value?"":",",value); first_value=0; }
static void signed_number(int64_t value)
{ printf("%s%" PRId64,first_value?"":",",value); first_value=0; }
static void end_event(void) { puts("]}"); }
static void fatal(struct task *task, int phase)
{
  int error=errno?errno:EIO;
  if (task) { begin_event("ERROR",task); number(error); number(phase); end_event(); }
  fprintf(stderr,"COLLECTOR_FAILURE phase=%d errno=%d\n",phase,error);
  exit(2); /* Kernel EXITKILL applies to every attached task; no invented END. */
}
static struct task *find_task(pid_t tid)
{
  for (size_t i=0;i<task_count;++i) if (tasks[i].alive && tasks[i].tid==tid) return &tasks[i];
  return NULL;
}
static struct task *birth(pid_t tid, struct task *parent)
{
  if (task_count==MAX_TASKS || find_task(tid)) { errno=EOVERFLOW; fatal(parent,10); }
  struct task *task=&tasks[task_count++];
  task->tid=tid; task->generation=task_count; task->alive=1; task->seed=1; ++live;
  begin_event("BIRTH",task);
  number(parent?parent->generation:0); number(parent?parent->clone_flags:0); end_event();
  return task;
}
static void fd_event(struct task *task, uint64_t call, int force)
{
  struct fd_record records[COLLECTOR_MAX_FDS];
  int count=snapshot_fds(task->tid,records,COLLECTOR_MAX_FDS);
  if (count<0) fatal(task,20);
  if (!force && count==task->fd_count && !memcmp(records,task->fds,(size_t)count*sizeof(*records))) return;
  begin_event("FDS",task); number(call); number((uint64_t)count);
  for (int i=0;i<count;++i) {
    number(records[i].fd); number(records[i].flags); number(records[i].dev);
    number(records[i].inode); number(records[i].mode); number(records[i].mount_id);
  }
  end_event(); task->fd_count=count;
  memcpy(task->fds,records,(size_t)count*sizeof(*records));
}
static int memory(pid_t tid, uint64_t address, void *destination, size_t bytes)
{
  for (size_t offset=0;offset<bytes;offset+=sizeof(long)) {
    long word=0;
    /* Raw Linux ptrace PEEK returns via data pointer; libc's wrapper differs. */
    if (trace(PTRACE_PEEKDATA,tid,(uintptr_t)address+offset,(uintptr_t)&word)<0) return -1;
    size_t left=bytes-offset;
    memcpy((char *)destination+offset,&word,left<sizeof(word)?left:sizeof(word));
  }
  return 0;
}
static int bpf_fd(uint64_t command)
{
  switch (command) { case 0: case 5: case 7: case 13: case 14: case 17: case 18:
    case 19: case 28: case 30: case 32: case 33: return 1; default:return 0; }
}
static int expected_fd_snapshot(struct task *task, int64_t result)
{
  if (result<0) return 0;
  switch (task->nr) {
    case 2: case 3: case 22: case 32: case 33: case 41: case 43: case 53: case 85:
    case 213: case 253: case 257: case 282: case 283: case 284: case 288: case 289:
    case 290: case 291: case 292: case 293: case 294: case 298: case 300: case 319:
    case 323: case 425: case 428: case 430: case 432: case 433: case 434: case 436:
    case 437: case 438: case 444: return 1;
    case 72: return task->args[1]==0 || task->args[1]==2 || task->args[1]==1030;
    case 317: return !!(task->args[1]&8);
    case 321: return bpf_fd(task->args[0]);
    default:return 0;
  }
}
static int may_change_fds(struct task *task, int64_t result)
{
  if (expected_fd_snapshot(task,result)) return 1;
  if (result<0) return 0;
  switch (task->nr) {
    /* Known non-FD-table-mutating returns; every other success is inspected. */
    case 0: case 1: case 4: case 5: case 6: case 7: case 8: case 9: case 10:
    case 11: case 12: case 13: case 14: case 15: case 17: case 18: case 19: case 20:
    case 21: case 23: case 24: case 25: case 28: case 35: case 39: case 61: case 62:
    case 63: case 72: case 73: case 74: case 75: case 79: case 80: case 81: case 82:
    case 83: case 84: case 87: case 88: case 89: case 90: case 91: case 92: case 93:
    case 94: case 95: case 96: case 97: case 98: case 99: case 100: case 102: case 104:
    case 105: case 106: case 107: case 108: case 110: case 111: case 115: case 116:
    case 117: case 118: case 119: case 120: case 121: case 122: case 123: case 125:
    case 126: case 127: case 128: case 129: case 130: case 131: case 132: case 137:
    case 138: case 157: case 158: case 161: case 186: case 202: case 217: case 218:
    case 228: case 229: case 230: case 231: case 234: case 262: case 267: case 273:
    case 302: case 310: case 311: case 318: case 332: case 334: case 424: return 0;
    default:return 1;
  }
}
static void syscall_entry(struct task *task, const struct ptrace_syscall_info *info)
{
  if (task->pending || info->arch!=AUDIT_ARCH_X86_64) { errno=EPROTO; fatal(task,30); }
  task->pending=1; task->seed=0; task->call=++call_count; task->nr=info->entry.nr;
  for (int i=0;i<6;++i) task->args[i]=info->entry.args[i];
  begin_event("ENTER",task); number(task->call); number(info->arch); number(task->nr);
  for (int i=0;i<6;++i) number(task->args[i]);
  end_event(); task->clone_flags=0; task->ioctl_kind=0;
  if (task->nr==SYS_clone) task->clone_flags=task->args[0];
  if (task->nr==SYS_clone3 && memory(task->tid,task->args[0],&task->clone_flags,8)) fatal(task,31);
  if (task->clone_flags&(CLONE_UNTRACED|CLONE_FILES|CLONE_THREAD)) {
    errno=ENOTSUP; fatal(task,32); /* Do not run a call whose descendants cannot be observed. */
  }
  if (task->nr==SYS_ioctl) {
    if (task->args[1]==SECCOMP_IOCTL_NOTIF_RECV) task->ioctl_kind=1;
    if (task->args[1]==SECCOMP_IOCTL_NOTIF_ADDFD) {
      task->ioctl_kind=2;
      if (memory(task->tid,task->args[2],&task->add,sizeof(task->add))) fatal(task,33);
    }
    if (task->args[1]==SECCOMP_IOCTL_NOTIF_SEND) {
      task->ioctl_kind=3;
      if (memory(task->tid,task->args[2],&task->reply,sizeof(task->reply))) fatal(task,34);
    }
  }
}
static void syscall_return(struct task *task, const struct ptrace_syscall_info *info)
{
  int64_t result=info->exit.rval;
  if (!task->pending) {
    if (!task->seed || result!=0) { errno=EPROTO; fatal(task,40); }
    begin_event("RETURN",task); number(0); signed_number(result); end_event(); task->seed=0;
    return;
  }
  begin_event("RETURN",task); number(task->call); signed_number(result); end_event();
  if (task->ioctl_kind==1 && result==0) {
    struct seccomp_notif request;
    if (memory(task->tid,task->args[2],&request,sizeof(request))) fatal(task,41);
    begin_event("NOTIFY_RECV",task); number(task->call); number(request.id); number(request.pid);
    number(request.flags); number((uint64_t)(unsigned int)request.data.nr); number(request.data.arch);
    number(task->args[0]); for (int i=0;i<6;++i) number(request.data.args[i]); end_event();
  } else if (task->ioctl_kind==2) {
    begin_event("ADDFD",task); number(task->call); number(task->add.id); number(task->add.flags);
    number(task->add.srcfd); number(task->add.newfd); number(task->add.newfd_flags);
    signed_number(result); end_event();
  } else if (task->ioctl_kind==3) {
    begin_event("NOTIFY_SEND",task); number(task->call); number(task->reply.id);
    signed_number(task->reply.val); signed_number(task->reply.error); number(task->reply.flags);
    signed_number(result); end_event();
  }
  if (may_change_fds(task,result)) fd_event(task,task->call,expected_fd_snapshot(task,result));
  task->pending=0;
}
static void resume(struct task *task, int signal)
{ if (trace(PTRACE_SYSCALL,task->tid,0,(uintptr_t)signal)) fatal(task,50); }

static void drain_output(void)
{
  char bytes[4096]; ssize_t count;
  while ((count=read(output_pipe,bytes,sizeof(bytes)))>0) {
    for (ssize_t i=0;i<count;++i) {
      if (output_size==sizeof(output_line)-1) { errno=EOVERFLOW; fatal(&tasks[0],60); }
      output_line[output_size++]=bytes[i];
      if (bytes[i]=='\n') {
        output_line[output_size]=0;
        if (!strncmp(output_line,"RAW_FIXTURE ",12)) fputs(output_line,stdout);
        else printf("FIXTURE_OUTPUT %s",output_line);
        output_size=0;
      }
    }
  }
  if (count<0 && errno!=EAGAIN && errno!=EINTR) fatal(&tasks[0],61);
}

int main(int argc, char **argv)
{
  if (getuid()!=0 || argc!=2) return 2;
  struct utsname kernel;
  if (uname(&kernel) || strcmp(kernel.release,"6.12.113+deb13-cloud-amd64") ||
      access("/etc/guest-collector-scope",R_OK)) return 2;
  int selected=atoi(argv[1]+(strlen(argv[1])>=2?2:0));
  char canonical[8]; snprintf(canonical,sizeof(canonical),"HF%02d",selected);
  if (selected<1 || selected>24 || strcmp(canonical,argv[1])) return 2;
  setvbuf(stdout,NULL,_IOLBF,0);
  int output[2]; if (pipe2(output,O_CLOEXEC)) return 2;
  pid_t root=fork();
  if (root<0) return 2;
  if (!root) {
    close(output[0]);
    if (dup2(output[1],1)<0 || dup2(output[1],2)<0) _exit(2);
    close(output[1]);
    if (trace(PTRACE_TRACEME,0,0,0) || raise(SIGSTOP)) _exit(2);
    execl("/harmless-fixtures","harmless-fixtures",canonical,(char *)NULL);
    _exit(2);
  }
  close(output[1]); output_pipe=output[0];
  if (fcntl(output_pipe,F_SETFL,O_NONBLOCK)) return 2;
  int status;
  if (waitpid(root,&status,0)!=root || !WIFSTOPPED(status) || WSTOPSIG(status)!=SIGSTOP) return 2;
  unsigned long options=PTRACE_O_TRACESYSGOOD|PTRACE_O_TRACEFORK|PTRACE_O_TRACEVFORK|
      PTRACE_O_TRACECLONE|PTRACE_O_TRACEEXEC|PTRACE_O_TRACEEXIT|PTRACE_O_EXITKILL;
  if (trace(PTRACE_SETOPTIONS,root,0,options)) return 2;
  printf("TRACE_BEGIN {\"version\":\"guest-syscall-fd-v1\",\"fixture_id\":\"%s\","
         "\"clock_domain\":\"GUEST_TRACER_OBSERVATION_MONOTONIC_NS\"}\n",canonical);
  struct task *first=birth(root,NULL); first->ready=1; fd_event(first,0,1); resume(first,0);
  int root_status=-1;
  while (live) {
    drain_output();
    pid_t tid=waitpid(-1,&status,__WALL|WNOHANG);
    if (tid==0) { struct pollfd descriptor={output_pipe,POLLIN,0}; poll(&descriptor,1,1); continue; }
    if (tid<0) { if (errno==EINTR) continue; fatal(first,70); }
    struct task *task=find_task(tid);
    if (!task) {
      if (!WIFSTOPPED(status) || WSTOPSIG(status)!=SIGSTOP ||
          ((unsigned int)status>>16) || early_count==MAX_TASKS) { errno=ESRCH; fatal(first,71); }
      for (int i=0;i<early_count;++i) if (early_stops[i]==tid) { errno=EPROTO; fatal(first,71); }
      early_stops[early_count++]=tid;
      continue;
    }
    if (WIFEXITED(status) || WIFSIGNALED(status)) {
      if (task->pending) {
        begin_event("ABORT",task); number(task->call);
        number(WIFSIGNALED(status)?(uint64_t)WTERMSIG(status):0); end_event(); task->pending=0;
      }
      begin_event("EXIT",task); number((uint64_t)status); end_event();
      task->alive=0; --live; if (tid==root) root_status=status;
      continue;
    }
    if (!WIFSTOPPED(status)) { errno=EPROTO; fatal(task,72); }
    int signal=WSTOPSIG(status), event=(unsigned int)status>>16;
    if (!task->ready) {
      if (signal!=SIGSTOP) { errno=EPROTO; fatal(task,73); }
      task->ready=1; fd_event(task,0,1); resume(task,0); continue;
    }
    if (signal==(SIGTRAP|0x80)) {
      struct ptrace_syscall_info info={0};
      long size=trace(PTRACE_GET_SYSCALL_INFO,tid,sizeof(info),(uintptr_t)&info);
      if (size<0) fatal(task,74);
      if (info.op==PTRACE_SYSCALL_INFO_ENTRY) syscall_entry(task,&info);
      else if (info.op==PTRACE_SYSCALL_INFO_EXIT) syscall_return(task,&info);
      else { errno=EPROTO; fatal(task,75); }
      resume(task,0); continue;
    }
    if (event) {
      unsigned long message=0;
      if (trace(PTRACE_GETEVENTMSG,tid,0,(uintptr_t)&message)) fatal(task,76);
      if (event==PTRACE_EVENT_FORK || event==PTRACE_EVENT_VFORK || event==PTRACE_EVENT_CLONE) {
        if (!task->pending) { errno=EPROTO; fatal(task,77); }
        struct task *child=birth((pid_t)message,task);
        for (int i=0;i<early_count;++i) if (early_stops[i]==child->tid) {
          early_stops[i]=early_stops[--early_count];
          child->ready=1; fd_event(child,0,1); resume(child,0); break;
        }
      } else if (event==PTRACE_EVENT_EXEC) {
        ++task->image; begin_event("EXEC",task); number(message); end_event(); fd_event(task,task->call,1);
      } else if (event==PTRACE_EVENT_EXIT) {
        fd_event(task,task->pending?task->call:0,0);
        begin_event("PRE_EXIT",task); number(message); end_event();
      } else { errno=ENOTSUP; fatal(task,78); }
      resume(task,0); continue;
    }
    siginfo_t info;
    if (trace(PTRACE_GETSIGINFO,tid,0,(uintptr_t)&info)) fatal(task,79);
    begin_event("SIGNAL",task); number((uint64_t)signal); signed_number(info.si_code); end_event();
    resume(task,signal);
  }
  drain_output(); close(output_pipe);
  if (early_count) { errno=EPROTO; fatal(first,81); }
  if (output_size) { errno=EPROTO; fatal(first,80); }
  printf("TRACE_END {\"events\":%" PRIu64 ",\"tasks\":%" PRIu64 ",\"live\":%d,\"root_status\":%d}\n",
         sequence,task_count,live,root_status);
  return root_status==0?0:2;
}
