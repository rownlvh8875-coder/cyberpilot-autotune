/* TEST ONLY fault injection around native component/libsd-bus boundary. */
#define main fm_fixture_main
#include "../../research/factory_manager/factory.c"
#undef main
#include <stdarg.h>
#include <dirent.h>
const char *fm_test_case="normal";
static pid_t factory_pid;
static int close_armed,close_fired,depth,properties[16];
static const char *last_property;
static int generation_reads,foreign_fd=-1;
static int is_case(const char *s){return !strcmp(fm_test_case,s);}
int __real_sd_bus_new(sd_bus **);
int __real_sd_bus_set_fd(sd_bus *,int,int);
int __wrap_sd_bus_new(sd_bus **b) {
 if(getpid()==factory_pid && is_case("constructor_before_library"))return -ENOMEM;
 return __real_sd_bus_new(b);
}
int __wrap_sd_bus_set_fd(sd_bus *b,int in,int out) {
 if(getpid()==factory_pid && is_case("constructor_before_transfer"))return -EIO;
 return __real_sd_bus_set_fd(b,in,out);
}
static int own_fd_count(void) {
 DIR *d=opendir("/proc/self/fd");if(!d)return -1;
 int count=0;struct dirent *entry;
 while((entry=readdir(d)))if(entry->d_name[0]!='.')++count;
 if(closedir(d))return -1;
 return count;
}
int __real_sd_bus_negotiate_fds(sd_bus *,int);
int __real_sd_bus_set_bus_client(sd_bus *,int);
int __real_sd_bus_get_bus_id(sd_bus *,sd_id128_t *);
int sd_bus_get_fd(sd_bus *);
int __wrap_sd_bus_negotiate_fds(sd_bus *b,int value) {
 return __real_sd_bus_negotiate_fds(b,getpid()==factory_pid && is_case("client_no_fds")?0:value);
}
int __wrap_sd_bus_set_bus_client(sd_bus *b,int value) {
 return __real_sd_bus_set_bus_client(b,getpid()==factory_pid && is_case("not_bus_client")?0:value);
}
int __wrap_sd_bus_get_bus_id(sd_bus *b,sd_id128_t *id) {
 int r=__real_sd_bus_get_bus_id(b,id);
 if(getpid()==factory_pid && ++generation_reads==2 && is_case("generation_changed"))id->bytes[0]^=1;
 if(getpid()==factory_pid && generation_reads==2 && is_case("bus_fd_reuse")) {
  int fd=sd_bus_get_fd(b);if(fd<0)_exit(96);
  close(fd);int replacement=open("/dev/null",O_RDONLY);
  if(replacement!=fd){if(dup2(replacement,fd)!=fd)_exit(96);close(replacement);}
  foreign_fd=fd;
 }
 return r;
}
int __real_sd_bus_send(sd_bus *,sd_bus_message *,uint64_t *);
int __real_sd_bus_call(sd_bus *,sd_bus_message *,uint64_t,sd_bus_error *,sd_bus_message **);
int __real_sd_bus_message_append_basic(sd_bus_message *,char,const void *);
int __real_sd_bus_message_open_container(sd_bus_message *,char,const char *);
int __real_sd_bus_message_close_container(sd_bus_message *);
int __real_close(int);
int __real_waitid(idtype_t,id_t,siginfo_t *,int);
long __real_syscall(long,...);
int __wrap_sd_bus_send(sd_bus *b,sd_bus_message *m,uint64_t *cookie) {
 return __real_sd_bus_send(b,m,cookie);
}
int __wrap_sd_bus_call(sd_bus *b,sd_bus_message *m,uint64_t timeout,sd_bus_error *error,sd_bus_message **reply) {
 const char *member=sd_bus_message_get_member(m);
 int start=member && !strcmp(member,"StartTransientUnit");
 if(start && is_case("start_error"))return -EIO;
 int r=__real_sd_bus_call(b,m,timeout,error,reply);
 if(start && is_case("cancel_after_submit"))return -ECANCELED;
 if(member && !strcmp(member,"Subscribe") && is_case("subscribe_cancel"))return -ECANCELED;
 if(member && !strcmp(member,"UnrefUnit"))close_armed=1;
 return r;
}
static int is_start(sd_bus_message *m) {
 const char *member=sd_bus_message_get_member(m);
 return getpid()==factory_pid && member && !strcmp(member,"StartTransientUnit");
}
int __wrap_sd_bus_message_append_basic(sd_bus_message *m,char type,const void *value) {
 if(is_start(m)) {
  if(type=='s') {
   const char *text=value;
   if(!strcmp(text,"AddRef") || !strcmp(text,"MemoryMax") || !strcmp(text,"StandardInputFileDescriptor"))last_property=text;
   if(is_case("bad_mode") && !strcmp(text,"fail"))value="replace";
  }
  if(type=='b' && last_property && !strcmp(last_property,"AddRef") && is_case("bad_addref")) {
   int zero=0;return __real_sd_bus_message_append_basic(m,type,&zero);
  }
  if(type=='h' && is_case("fd_wrong_type")) {
   int fd=open("/dev/null",O_RDONLY|O_CLOEXEC);
   int r=__real_sd_bus_message_append_basic(m,type,&fd);close(fd);return r;
  }
  if(type=='t' && last_property && !strcmp(last_property,"MemoryMax") && is_case("bad_limit")) {
   uint64_t unlimited=UINT64_MAX;return __real_sd_bus_message_append_basic(m,type,&unlimited);
  }
 }
 return __real_sd_bus_message_append_basic(m,type,value);
}
int __wrap_sd_bus_message_open_container(sd_bus_message *m,char type,const char *signature) {
 if(is_start(m)) {
  if(depth>=16)_exit(96);
  properties[depth++]=type=='a' && !strcmp(signature,"(sv)");
  if(type=='v' && last_property && !strcmp(last_property,"StandardInputFileDescriptor") && is_case("bad_signature"))
   signature="u";
 }
 return __real_sd_bus_message_open_container(m,type,signature);
}
int __wrap_sd_bus_message_close_container(sd_bus_message *m) {
 if(is_start(m) && depth>0) {
  if(properties[depth-1] && (is_case("extra_property") || is_case("extra_fd") || is_case("duplicate_property"))) {
   int fd=-1;
   if(__real_sd_bus_message_open_container(m,'r',"sv")<0 ||
      __real_sd_bus_message_append_basic(m,'s',is_case("duplicate_property")?"AddRef":"Unexpected")<0 ||
      __real_sd_bus_message_open_container(m,'v',is_case("extra_fd")?"h":"s")<0)_exit(96);
   if(is_case("extra_fd")) {
    fd=open("/dev/null",O_RDONLY|O_CLOEXEC);
    if(fd<0 || __real_sd_bus_message_append_basic(m,'h',&fd)<0)_exit(96);
    __real_close(fd);
   } else if(__real_sd_bus_message_append_basic(m,'s',"extra")<0)_exit(96);
   if(__real_sd_bus_message_close_container(m)<0 || __real_sd_bus_message_close_container(m)<0)_exit(96);
  }
  --depth;
 }
 return __real_sd_bus_message_close_container(m);
}
int __wrap_close(int fd) {
 int r=__real_close(fd);
 if(getpid()==factory_pid && close_armed && !close_fired && is_case("close_unknown")) {
  close_fired=1;errno=EINTR;return -1;
 }
 return r;
}
int __wrap_waitid(idtype_t type,id_t id,siginfo_t *info,int options) {
 int r=__real_waitid(type,id,info,options);
 if((getpid()==factory_pid && is_case("wait_unknown")) || (getpid()!=factory_pid && is_case("manager_wait_unknown"))){errno=EINTR;return -1;}
 return r;
}
long __wrap_syscall(long n,...) {
 va_list ap;va_start(ap,n);unsigned long a[6]={0};unsigned count=0;
 switch(n) {
 case SYS_kcmp:count=5;break;case SYS_clone3:count=2;break;
 case SYS_close_range:count=3;break;case SYS_pidfd_send_signal:count=4;break;
 default:_exit(96);
 }
 for(unsigned i=0;i<count;++i)a[i]=va_arg(ap,unsigned long);
 va_end(ap);
 long result=__real_syscall(n,a[0],a[1],a[2],a[3],a[4],a[5]);
 if(n==SYS_clone3 && result>0 && getpid()!=factory_pid && is_case("clone_return_uncertain")) {
  errno=ECANCELED;return -1;
 }
 return result;
}
int main(int argc,char **argv) {
 if(argc!=2)return 96;
 fm_test_case=argv[1];factory_pid=getpid();
 int before=own_fd_count();
 int result=fm_fixture_main();
 if(!strncmp(fm_test_case,"constructor_",12) && own_fd_count()!=before)fprintf(stderr,"constructor native FD leak\n");
 if(foreign_fd>=0 && fcntl(foreign_fd,F_GETFD)<0)_exit(98);
 if(is_case("twice"))return fm_fixture_main();
 return result;
}
