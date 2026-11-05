/* TEST ONLY: current fresh fixture root + fault injection; never built as host backend. */
#define _GNU_SOURCE
#include "../../research/factory_intent/internal.h"
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/random.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <time.h>
#include <unistd.h>
const char *fm_test_case="normal";
static const char *which;
static pid_t owner;
static int leaf=-1,root=-1,leaf_anchor=-1,root_anchor=-1,foreign=-1,fired,close_fired,scope_calls,writes,filesyncs,rootsyncs,bad_start;
static int caller(void){return getpid()==owner;}
static int is(const char *name){return caller() && !strcmp(which,name);}
int __real_openat(int,const char *,int,...);
int __real_close(int);
int __real_fcntl(int,int,...);
ssize_t __real_write(int,const void *,size_t);
ssize_t __real_pread(int,void *,size_t,off_t);
int __real_fsync(int);
int __real_clock_gettime(clockid_t,struct timespec *);
ssize_t __real_getrandom(void *,size_t,unsigned);
static void pause_here(void) {
 alarm(4); /* fixed child remains bounded even if the test harness disappears */
 if(__real_write(1,"PAUSED\n",7)!=7)_exit(96);
 for(;;)pause();
}
int fi_open_scope(struct fi_scope *s) {
 ++scope_calls;
 int b=open(".",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 if(fi_capture_ref(&s->base,b))return -1;
 int r=__real_openat(b,"state",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 root=r;
 if(is("scope_partial")) {s->root.fd=r;return -1;}
 if(fi_capture_ref(&s->root,r))return -1;
 return 0;
}
int __wrap_fcntl(int fd,int cmd,...) {
 va_list ap;va_start(ap,cmd);int arg=0;
 if(cmd==F_DUPFD_CLOEXEC || cmd==F_SETFD || cmd==F_DUPFD)arg=va_arg(ap,int);
 va_end(ap);
 if(is("anchor_failure") && fd==leaf && cmd==F_DUPFD_CLOEXEC){errno=EMFILE;return -1;}
 int result=__real_fcntl(fd,cmd,arg);
 if(caller() && cmd==F_DUPFD_CLOEXEC) {
  if(fd==leaf)leaf_anchor=result;
  if(fd==root)root_anchor=result;
 }
 return result;
}
int __wrap_openat(int dir,const char *name,int flags,...) {
 va_list ap;va_start(ap,flags);mode_t mode=0;
 if(flags&O_CREAT)mode=(mode_t)va_arg(ap,int);
 va_end(ap);
 int r=__real_openat(dir,name,flags,mode);
 if(caller() && !strcmp(name,"attempt.intent") && (flags&O_CREAT)) {
  leaf=r;
  if(r>=0 && is("pause_after_create"))pause_here();
  if(r>=0 && is("open_unknown")){errno=EINTR;return -1;}
 }
 return r;
}
ssize_t __wrap_write(int fd,const void *data,size_t n) {
 if(caller() && fd==leaf) {
  ++writes;
  if(is("zero_write"))return 0;
  if(is("negative_write")){errno=EIO;return -1;}
  if(is("partial_write"))return __real_write(fd,data,n-1);
  ssize_t r=__real_write(fd,data,n);
  if(is("write_unknown")){errno=EINTR;return -1;}
  return r;
 }
 return __real_write(fd,data,n);
}
static void replace_fd(int fd,int same) {
 int replacement=same?__real_openat(root,"attempt.intent",O_RDWR|O_CLOEXEC):
  open("/dev/null",O_RDWR|O_CLOEXEC);
 if(replacement<0 || dup2(replacement,fd)!=fd)_exit(96);
 if(replacement!=fd)__real_close(replacement);
 foreign=fd;
}
int __wrap_fsync(int fd) {
 if(caller() && fd==leaf) {
  ++filesyncs;
  if(is("file_fsync")){errno=EIO;return -1;}
  if(is("file_fsync_unknown")){__real_fsync(fd);errno=EINTR;return -1;}
 }
 if(caller() && fd==root) {
  ++rootsyncs;
  if(is("root_fsync")){errno=EIO;return -1;}
  if(is("root_fsync_unknown")){__real_fsync(fd);errno=EINTR;return -1;}
 }
 int r=__real_fsync(fd);
 if(caller() && fd==leaf && !fired) {
  fired=1;
  if(is("tamper")){unsigned char x=7;if(pwrite(leaf,&x,1,0)!=1)_exit(96);}
  if(is("file_mode") && fchmod(leaf,0640))_exit(96);
  if(is("root_mode") && fchmod(root,0750))_exit(96);
  if(is("file_hardlink") && linkat(root,"attempt.intent",root,"extra",0))_exit(96);
  if(is("leaf_unlink") && unlinkat(root,"attempt.intent",0))_exit(96);
  if(is("leaf_replace")) {
   if(renameat(root,"attempt.intent",root,"original"))_exit(96);
   int f=__real_openat(root,"attempt.intent",O_CREAT|O_EXCL|O_RDWR|O_CLOEXEC,0600);
   if(f<0)_exit(96);
   __real_close(f);
  }
  if(is("root_replace")) {
   if(rename("state","original-state") || mkdir("state",0700))_exit(96);
  }
  if(is("file_fd_reuse") || is("file_same_inode_reuse"))replace_fd(leaf,is("file_same_inode_reuse"));
  if(is("root_fd_reuse"))replace_fd(root,0);
  if(is("file_socket_reuse") || is("root_socket_reuse")) {
   int pair[2],target=is("file_socket_reuse")?leaf:root;
   if(socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,pair) || dup2(pair[0],target)!=target)_exit(96);
   __real_close(pair[0]);__real_close(pair[1]);foreign=target;
  }
  if(is("root_same_inode_reuse")) {
   int f=open("state",O_RDONLY|O_DIRECTORY|O_CLOEXEC);
   if(f<0 || dup2(f,root)!=root)_exit(96);
   if(f!=root)__real_close(f);
   foreign=root;
  }
 }
 if(caller() && fd==root && is("pause_after_durable"))pause_here();
 return r;
}
ssize_t __wrap_pread(int fd,void *data,size_t n,off_t off) {
 if(is("read_unknown") && fd==leaf){errno=EINTR;return -1;}
 ssize_t r=__real_pread(fd,data,n,off);
 return is("short_read") && fd==leaf && r>0?r-1:r;
}
ssize_t __real___pread_chk(int,void *,size_t,off_t,size_t);
ssize_t __wrap___pread_chk(int fd,void *data,size_t n,off_t off,size_t bound) {
 if(is("read_unknown") && fd==leaf){errno=EINTR;return -1;}
 ssize_t r=__real___pread_chk(fd,data,n,off,bound);
 return is("short_read") && fd==leaf && r>0?r-1:r;
}
int __wrap_clock_gettime(clockid_t c,struct timespec *t) {
 if(is("clock_failure")){errno=EIO;return -1;}
 int r=__real_clock_gettime(c,t);
 if(is("clock_invalid"))t->tv_nsec=1000000000;
 return r;
}
ssize_t __wrap_getrandom(void *b,size_t n,unsigned f) {
 if(is("random_failure")){errno=EIO;return -1;}
 ssize_t r=__real_getrandom(b,n,f);
 return is("random_short") && r>0?r-1:r;
}
static void foreign_anchor(int anchor,int directory) {
 int f=directory?open("state",O_RDONLY|O_DIRECTORY|O_CLOEXEC):
  __real_openat(root,"attempt.intent",O_RDWR|O_CLOEXEC);
 if(f<0 || dup2(f,anchor)!=anchor)_exit(96);
 if(f!=anchor)__real_close(f);
 foreign=anchor;
}
int __wrap_close(int fd) {
 if(caller() && !close_fired &&
    ((fd==leaf && is("leaf_anchor_reuse")) || (fd==root && is("root_anchor_reuse")))) {
  close_fired=1;
  int r=__real_close(fd);
  foreign_anchor(fd==root?root_anchor:leaf_anchor,fd==root);
  return r; /* crucial: successful primary close, foreign same-inode anchor */
 }
 if(caller() && fd==leaf && !close_fired && (is("close_unknown") || is("close_fd_reuse"))) {
  close_fired=1;
  int r=__real_close(fd);
  if(is("close_fd_reuse")) {
   int f=open("/dev/null",O_RDWR|O_CLOEXEC);
   if(f<0 || dup2(f,fd)!=fd)_exit(96);
   if(f!=fd)__real_close(f);
   foreign=fd;
  }
  (void)r;errno=EINTR;return -1;
 }
 return __real_close(fd);
}
int __real_sd_bus_call(void *,void *,unsigned long,void *,void **);
int __wrap_sd_bus_call(void *bus,void *message,unsigned long timeout,void *error,void **reply);
#include "../../research/factory_manager/sdbus_abi.h"
int __wrap_sd_bus_call(void *bus,void *message,unsigned long timeout,void *error,void **reply) {
 const char *member=sd_bus_message_get_member(message);
 if(caller() && member && !strcmp(member,"StartTransientUnit") && (writes!=1 || filesyncs!=1 || rootsyncs!=1))++bad_start;
 int r=__real_sd_bus_call(bus,message,timeout,error,reply);
 if(caller() && member && !strcmp(member,"UnrefUnit") && is("post_manager_tamper")) {
  unsigned char x=9;if(pwrite(leaf,&x,1,0)!=1)_exit(96);
 }
 return r;
}
long __real_syscall(long,...);
long __wrap_syscall(long n,...) {
 va_list ap;va_start(ap,n);unsigned long a[6]={0};unsigned count=0;
 switch(n) {
 case SYS_kcmp:count=5;break;case SYS_clone3:count=2;break;
 case SYS_close_range:count=3;break;case SYS_pidfd_send_signal:count=4;break;
 default:_exit(96);
 }
 for(unsigned k=0;k<count;++k)a[k]=va_arg(ap,unsigned long);
 va_end(ap);
 long r=__real_syscall(n,a[0],a[1],a[2],a[3],a[4],a[5]);
 if(n==SYS_close_range && !caller() && r==0 && a[0]<=3 && a[1]>=1024) {
  /* Immediately after inherited-FD sweep; no later allocator can reuse them yet. */
  if((root>=3 && __real_fcntl(root,F_GETFD)>=0) ||
     (leaf>=3 && __real_fcntl(leaf,F_GETFD)>=0))_exit(98);
 }
 return r;
}
int main(int argc,char **argv) {
 if(argc!=2)return 96;
 which=argv[1];owner=getpid();
 if(is("manager_failure"))fm_test_case="failed_job";
 /* Capture summary for test counters without changing production report semantics. */
 int pipes[2];if(pipe2(pipes,O_CLOEXEC))return 96;
 int output=dup(1);if(output<0 || dup2(pipes[1],1)!=1)return 96;
 __real_close(pipes[1]);
 /* pause cases must notify the original harness pipe directly. */
 if(!strncmp(which,"pause_",6)) {
  if(dup2(output,1)!=1)return 96;
  return fi_run_fixed();
 }
 int r=fi_run_fixed();
 if(is("twice"))r=fi_run_fixed();
 fflush(stdout);if(dup2(output,1)!=1)return 96;__real_close(output);
 char all[8192];ssize_t n=read(pipes[0],all,sizeof all-1);__real_close(pipes[0]);
 if(n<=0)return 96;
 all[n]=0;
 char *last=all,*next;
 for(char *it=all;(next=strchr(it,'\n'))!=NULL;it=next+1)if(next[1])last=next+1;
 char *end=strchr(last,'}');if(!end)return 96;
 *end=0;
 if(last!=all && __real_write(1,all,(size_t)(last-all))!=(ssize_t)(last-all))return 96;
 printf("%s,\"write_calls\":%d,\"file_fsync_calls\":%d,\"root_fsync_calls\":%d,"
  "\"scope_calls\":%d,\"start_after_intent_failure\":%d,\"foreign_fd_open\":%s}\n",
  last,writes,filesyncs,rootsyncs,scope_calls,bad_start,
  foreign>=0 && __real_fcntl(foreign,F_GETFD)>=0?"true":"false");
 return r;
}
