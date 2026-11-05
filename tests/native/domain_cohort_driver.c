/* TEST ONLY virtual cgroup boundary on fresh ordinary private directories. */
#include "cohort_driver_reference.c"
#include <sys/statfs.h>
struct dr_test_audit {
 atomic_uint created,births,kills,waits,removed,foreign_closes;
};
static struct dr_test_audit *da;
static int virtual_P=-1,virtual_D=-1,kill_handle=-1,original_worker=-1;
static int replaced,foreign_D=-1,stat_reads,domain_close_fired;
static int live_domain_fd=-1,w_clock_armed,w_clock_fired;
static char D_name[48];
static struct stat D_identity;
int __real_openat(int,const char *,int,...);
ssize_t __real_write(int,const void *,size_t);
int __real_fstatfs(int,struct statfs *);
int __real_unlinkat(int,const char *,int);
static void file_set(int dir,const char *name,const char *text,int fresh) {
 int fd=__real_openat(dir,name,O_WRONLY|O_CLOEXEC|O_NOFOLLOW|
                      (fresh?O_CREAT|O_EXCL:O_TRUNC),0600);
 size_t n=strlen(text);
 if(fd<0 || (n && __real_write(fd,text,n)!=(ssize_t)n) || __real_close(fd))_exit(96);
}
int __wrap_fstatfs(int fd,struct statfs *fs) {
 int r=__real_fstatfs(fd,fs);
 if(!r && role==2 && !named("unbound_regular_P")) {
  if(virtual_P<0) {
   virtual_P=fcntl(fd,F_DUPFD_CLOEXEC,3);
   if(virtual_P<0)_exit(96);
   if(named("P_partial_same_inode")) {
    if(__real_close(fd))_exit(96);
    int n=__real_openat(virtual_P,".",O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    if(n!=fd){if(dup2(n,fd)!=fd)_exit(96);__real_close(n);}
    foreign_D=fd;errno=EIO;return -1;
   }
   file_set(virtual_P,"cgroup.type",named("P_threaded")?"threaded\n":"domain\n",1);
  }
  fs->f_type=0x63677270;
 }
 return r;
}
int __real_poll(struct pollfd *,nfds_t,int);
int __wrap_poll(struct pollfd *p,nfds_t n,int ms) {
 int r=__real_poll(p,n,ms);
 if(role==2 && n==1 && p[0].fd==original_worker && ms==0 && r==0)w_clock_armed=1;
 return r;
}
int __wrap___poll_chk(struct pollfd *p,nfds_t n,int ms,size_t capacity) {
 if(n>capacity/sizeof *p){errno=EINVAL;return -1;}
 return __wrap_poll(p,n,ms);
}
int __wrap_clock_gettime(clockid_t id,struct timespec *t) {
 if(role==2 && named("W_generation_clock_once") && w_clock_armed && !w_clock_fired++) {
  errno=EIO;return -1;
 }
 return dr_reference_clock_gettime(id,t);
}
int __wrap_mkdirat(int parent,const char *name,mode_t mode) {
 if(role==2 && named("D_create_error")){errno=EIO;return -1;}
 int r=dr_reference_mkdirat(parent,name,mode);
 if(!r && role==2 && !strncmp(name,"owned-d-",8)) {
  atomic_fetch_add(&da->created,1);
  strcpy(D_name,name);
  virtual_D=__real_openat(parent,name,O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);
  if(virtual_D<0 || fstat(virtual_D,&D_identity))_exit(96);
  file_set(virtual_D,"cgroup.type","domain\n",1);
  file_set(virtual_D,"cgroup.procs","",1);
  file_set(virtual_D,"cgroup.events","populated 0\nfrozen 0\n",1);
  if(!named("missing_stat"))
   file_set(virtual_D,"cgroup.stat",named("descendants")?
    "nr_descendants 1\nnr_dying_descendants 0\n":"nr_descendants 0\nnr_dying_descendants 0\n",1);
  file_set(virtual_D,"cgroup.kill","",1);
 }
 return r;
}
int __wrap_openat(int fd,const char *name,int flags,...) {
 unsigned mode=0;
 if(flags&O_CREAT){va_list ap;va_start(ap,flags);mode=va_arg(ap,unsigned);va_end(ap);}
 if(role==2 && !strncmp(name,"owned-d-",8) && (flags&O_DIRECTORY) && named("D_open_error")) {
  errno=EACCES;return -1;
 }
 if(role==2 && !strcmp(name,"cgroup.kill") && named("kill_open_error")){errno=EACCES;return -1;}
 if(role==2 && !strcmp(name,"cgroup.stat") && ++stat_reads==3 && named("late_descendant"))
  file_set(virtual_D,"cgroup.stat","nr_descendants 1\nnr_dying_descendants 0\n",0);
 int result=__real_openat(fd,name,flags,mode);
 if(role==2 && !strcmp(name,"cgroup.kill") && (flags&O_ACCMODE)==O_WRONLY)kill_handle=result;
 return result;
}
ssize_t __wrap_write(int fd,const void *data,size_t n) {
 if(role==2 && fd==kill_handle && kill_handle>=0) {
  atomic_fetch_add(&da->kills,1);
  if(n!=2 || memcmp(data,"1\n",2) || original_worker<0)_exit(96);
  if(named("kill_partial") || named("kill_unknown")) {
   if(__real_write(fd,data,1)!=1)_exit(96);
   errno=EIO;return named("kill_partial")?1:-1;
  }
  ssize_t r=__real_write(fd,data,n);
  if(named("not_sigkill")) {
   (void)poll(NULL,0,4700);
  } else if(__real_syscall(SYS_pidfd_send_signal,original_worker,SIGKILL,NULL,0))_exit(96);
  file_set(virtual_D,"cgroup.procs","",0);
  file_set(virtual_D,"cgroup.events",named("events_populated")?"populated 1\n":
   (named("events_duplicate")?"populated 0\npopulated 1\n":
    (named("events_missing")?"frozen 0\n":"populated 0\nfrozen 0\n")),0);
  return r;
 }
 return __real_write(fd,data,n);
}
int __wrap_close(int fd) {
 if(role==2 && fd==foreign_D)atomic_fetch_add(&da->foreign_closes,1);
 int is_kill=role==2 && fd==kill_handle;
 if(is_kill)kill_handle=-1;
 int r=dr_reference_close(fd);
 if((is_kill && named("kill_close_unknown")) ||
    (role==2 && fd==live_domain_fd && named("D_close_unknown") && !domain_close_fired++)) {
  errno=EINTR;return -1;
 }
 return r;
}
int __wrap_waitid(idtype_t type,id_t id,siginfo_t *info,int flags) {
 if(role==2)atomic_fetch_add(&da->waits,1);
 int r=dr_reference_waitid(type,id,info,flags);
 if(role==2 && named("domain_wait_exit137") && !r) {
  info->si_code=CLD_EXITED;info->si_status=137;
 }
 if(role==2 && named("domain_wait_unknown")){errno=EINTR;return -1;}
 return r;
}
int __wrap_unlinkat(int parent,const char *name,int flags) {
 if(role==2 && flags==AT_REMOVEDIR && !strcmp(name,D_name)) {
  struct stat a,b;
  if(fstatat(parent,name,&a,AT_SYMLINK_NOFOLLOW) || fstat(virtual_D,&b) ||
     a.st_dev!=b.st_dev || a.st_ino!=b.st_ino)_exit(96);
  if(named("D_unlink_error")){errno=EACCES;return -1;}
  const char *files[]={"cgroup.type","cgroup.procs","cgroup.events","cgroup.stat","cgroup.kill"};
  for(unsigned i=0;i<5;++i)if(__real_unlinkat(virtual_D,files[i],0))_exit(96);
  int r=__real_unlinkat(parent,name,flags);
  if(!r) {
   atomic_fetch_add(&da->removed,1);
   if(__real_unlinkat(virtual_P,"cgroup.type",0))_exit(96);
  }
  if(!r && named("D_unlink_unknown")){errno=EIO;return -1;}
  return r;
 }
 return __real_unlinkat(parent,name,flags);
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
 if(role==2 && nr==SYS_kcmp && atomic_load(&da->births)>0 && !replaced &&
    (named("name_replaced") || named("D_fd_reused"))) {
  struct stat st;
  if(!fstat((int)a[3],&st) && st.st_dev==D_identity.st_dev && st.st_ino==D_identity.st_ino) {
   replaced=1;
   if(named("name_replaced")) {
    if(renameat(virtual_P,D_name,virtual_P,"retained-original-D") ||
       __real_mkdirat(virtual_P,D_name,0700))_exit(96);
   } else {
    int fd=(int)a[3];if(__real_close(fd))_exit(96);
    int n=open(".",O_RDONLY|O_DIRECTORY|O_CLOEXEC);
    if(n!=fd){if(dup2(n,fd)!=fd)_exit(96);__real_close(n);}
    foreign_D=fd;errno=EBADF;return -1;
   }
  }
 }
 if(role==2 && nr==SYS_clone3) {
  struct clone_args *requested=(struct clone_args *)a[0],copy=*requested;
  struct stat st;
  if(copy.flags!=(CLONE_PIDFD|CLONE_INTO_CGROUP) || fstat((int)copy.cgroup,&st) ||
     st.st_dev!=D_identity.st_dev || st.st_ino!=D_identity.st_ino)_exit(96);
  live_domain_fd=(int)copy.cgroup;
  atomic_fetch_add(&da->births,1);
  copy.flags &= ~CLONE_INTO_CGROUP;copy.cgroup=0;
  long r=dr_reference_syscall(nr,&copy,a[1]);
  if(role==2) {
   original_worker=*(int *)(uintptr_t)copy.pidfd;
   if(r>0) {
    char text[128];
    if(named("members_extra"))snprintf(text,sizeof text,"%ld\n1\n",r);
    else if(named("members_E"))snprintf(text,sizeof text,"%ld\n%ld\n",r,(long)getpid());
    else snprintf(text,sizeof text,"%ld\n",r);
    file_set(virtual_D,"cgroup.procs",text,0);
    file_set(virtual_D,"cgroup.events","populated 1\n",0);
   }
  }
  return r;
 }
 return dr_reference_syscall(nr,a[0],a[1],a[2],a[3],a[4],a[5]);
}
int main(int argc,char **argv) {
 da=mmap(NULL,sizeof *da,PROT_READ|PROT_WRITE,MAP_SHARED|MAP_ANONYMOUS,-1,0);
 if(da==MAP_FAILED)return 96;
 int r=dr_driver_main(argc,argv);
 printf("{\"domain_audit\":{\"D_created\":%u,\"birth_into_D_requests\":%u,"
  "\"kill_writes\":%u,\"original_worker_waits\":%u,\"D_removed\":%u,"
  "\"foreign_close_attempts\":%u,\"containment\":\"SIMULATED\"}}\n",
  atomic_load(&da->created),atomic_load(&da->births),atomic_load(&da->kills),
  atomic_load(&da->waits),atomic_load(&da->removed),atomic_load(&da->foreign_closes));
 if(munmap(da,sizeof *da))return 96;
 return r;
}
