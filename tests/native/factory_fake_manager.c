/* TEST ONLY synthetic manager. Real private sd-bus wire, never PID1 or a service.
 * Fixed E probe only; no arbitrary executable, cgroup, credentials, P/D/W grant. */
#define main fm_manager_reference_main
#include "../../research/parent_handoff/handoff.c"
#undef main
#include "../../research/factory_manager/internal.h"
extern const char *fm_test_case;
static int is_case(const char *s) {return !strcmp(fm_test_case,s);}
static int e_probe(pid_t manager) {
 int null=open("/dev/null",O_RDWR|O_CLOEXEC);
 if(null<0 || dup2(null,1)!=1 || dup2(null,2)!=2 || getppid()!=manager ||
    syscall(SYS_close_range,3u,~0u,0u))return 20;
 struct channel c={.fd=-1,.anchor=-1};struct frame f={0};unsigned char ctx[CTX];int ok=0;
 if(channel_init(&c,0) || read_frame(&c,&f,0) || f.len!=CTX ||
    memcmp(f.data,"FME1\1\1\0\0\0\0",10))goto done;
 memcpy(ctx,f.data,CTX);
 if(is_case("e_wrong_nonce"))ctx[49]^=1;
 if(send_stage(&c,ctx,2,1) || read_frame(&c,&f,0) ||
    !check_frame(&f,ctx,3,2,CTX) || end_of_stream(&c) ||
    send_stage(&c,ctx,4,3))goto done;
 if(is_case("e_extra")) {unsigned char b=7;if(send(c.fd,&b,1,MSG_NOSIGNAL)!=1)goto done;}
 if(!is_case("e_no_shutdown") && shutdown(c.fd,SHUT_WR))goto done;
 ok=1;
done:
 frame_clear(&f);channel_close(&c);return ok && !uncertain?0:20;
}
static int parse_request(sd_bus_message *m,char unit[96],int *endpoint,int *borrowed,struct stat *identity) {
 const char *name,*mode;
 if(!sd_bus_message_has_signature(m,"ssa(sv)a(sa(sv))") ||
    sd_bus_message_read(m,"ss",&name,&mode)<=0 || strcmp(mode,"fail") ||
    strlen(name)!=64 || strncmp(name,"cyberpilot-native-e-lab-",24) ||
    strcmp(name+56,".service"))return -1;
 for(unsigned i=24;i<56;++i)if(!((name[i]>='0' && name[i]<='9') || (name[i]>='a' && name[i]<='f')))return -1;
 strcpy(unit,name);
 const char *keys[]={"Type","User","Group","Restart","DelegateSubgroup","AddRef","NoNewPrivileges",
  "CapabilityBoundingSet","AmbientCapabilities","RuntimeMaxUSec","TimeoutStartUSec","TimeoutStopUSec",
  "MemoryMax","MemorySwapMax","TasksMax","CPUQuotaPerSecUSec","DelegateControllers","ExecStart","StandardInputFileDescriptor"};
 unsigned seen=0;int r;
 if(sd_bus_message_enter_container(m,'a',"(sv)")<=0)return -1;
 while((r=sd_bus_message_enter_container(m,'r',"sv"))>0) {
  const char *key;if(sd_bus_message_read(m,"s",&key)<=0)return -1;
  unsigned k;for(k=0;k<19 && strcmp(key,keys[k]);++k){}
  if(k==19 || (seen&(1u<<k)))return -1;
  seen|=1u<<k;
  const char *signature=k<5?"s":(k<7?"b":(k<16?"t":(k==16?"as":(k==17?"a(sasb)":"h"))));
  if(sd_bus_message_enter_container(m,'v',signature)<=0)return -1;
  if(k<5) {
   const char *want[]={"exec","cp-e-lab","cp-e-lab","no",".supervisor"},*value;
   if(sd_bus_message_read(m,"s",&value)<=0 || strcmp(value,want[k]))return -1;
  } else if(k<7) {
   int value;if(sd_bus_message_read(m,"b",&value)<=0 || value!=1)return -1;
  } else if(k<16) {
   const uint64_t values[]={192,192,30000000,5000000,5000000,134217728,0,8,250000};uint64_t value;
   if(sd_bus_message_read(m,"t",&value)<=0 || value!=values[k-7])return -1;
  } else if(k==16) {
   if(sd_bus_message_enter_container(m,'a',"s")<=0)return -1;
   const char *want[]={"cpu","memory","pids"};
   for(unsigned i=0;i<3;++i){const char *value;if(sd_bus_message_read(m,"s",&value)<=0 || strcmp(value,want[i]))return -1;}
   if(sd_bus_message_at_end(m,0)<=0 || sd_bus_message_exit_container(m)<0)return -1;
  } else if(k==17) {
   const char *path,*arg;int ignore;
   if(sd_bus_message_enter_container(m,'a',"(sasb)")<=0 || sd_bus_message_enter_container(m,'r',"sasb")<=0 ||
      sd_bus_message_read(m,"s",&path)<=0 || strcmp(path,"/usr/local/lib/cyberpilot-native-e-lab/e-bootstrap") ||
      sd_bus_message_enter_container(m,'a',"s")<=0 || sd_bus_message_read(m,"s",&arg)<=0 || strcmp(path,arg) ||
      sd_bus_message_at_end(m,0)<=0 || sd_bus_message_exit_container(m)<0 ||
      sd_bus_message_read(m,"b",&ignore)<=0 || ignore ||
      sd_bus_message_exit_container(m)<0 || sd_bus_message_at_end(m,0)<=0 ||
      sd_bus_message_exit_container(m)<0)return -1;
  } else {
   int fd;struct stat st;int type=0,domain=0;socklen_t size=sizeof type;
   if(sd_bus_message_read(m,"h",&fd)<=0 || fstat(fd,&st) || !S_ISSOCK(st.st_mode) ||
      getsockopt(fd,SOL_SOCKET,SO_TYPE,&type,&size) || type!=SOCK_STREAM)return -1;
   size=sizeof domain;
   if(getsockopt(fd,SOL_SOCKET,SO_DOMAIN,&domain,&size) || domain!=AF_UNIX ||
      fcntl(fd,F_GETFD)<0 || !(fcntl(fd,F_GETFD)&FD_CLOEXEC))return -1;
   *endpoint=fcntl(fd,F_DUPFD_CLOEXEC,3);*borrowed=fd;*identity=st;
   if(*endpoint<0 || !same_ofd(fd,*endpoint))return -1;
  }
  if(sd_bus_message_at_end(m,0)<=0 || sd_bus_message_exit_container(m)<0 ||
     sd_bus_message_at_end(m,0)<=0 || sd_bus_message_exit_container(m)<0)return -1;
 }
 if(r<0 || seen!=((1u<<19)-1) || sd_bus_message_exit_container(m)<0 ||
    sd_bus_message_enter_container(m,'a',"(sa(sv))")<=0 || sd_bus_message_at_end(m,0)<=0 ||
    sd_bus_message_exit_container(m)<0 || sd_bus_message_at_end(m,1)<=0)return -1;
 return 0;
}
static int job_signal(sd_bus *bus,const char *unit) {
 sd_bus_message *signal=NULL;int result=-1;
 const char *path=is_case("wrong_job")?"/org/freedesktop/systemd1/job/2":"/org/freedesktop/systemd1/job/1";
 if(sd_bus_message_new_signal(bus,&signal,FM_PATH,FM_IFACE,"JobRemoved")<0)goto done;
 if(is_case("event_wrong_sender") && sd_bus_message_set_sender(signal,":1.9")<0)goto done;
 if(sd_bus_message_append(signal,"uoss",1u,path,is_case("wrong_unit")?"foreign.service":unit,
   is_case("failed_job")?"failed":"done")<0 || sd_bus_send(bus,signal,NULL)<0)goto done;
 result=0;
done:
 sd_bus_message_unref(signal);return result;
}
static int owner_signal(sd_bus *bus) {
 sd_bus_message *s=NULL;int result=-1;
 if(sd_bus_message_new_signal(bus,&s,FM_DBUS_PATH,FM_DBUS_IFACE,"NameOwnerChanged")<0)goto done;
 if(sd_bus_message_set_sender(s,FM_DBUS_IFACE)<0 ||
    sd_bus_message_append(s,"sss",FM_DEST,":1.0",":1.9")<0 || sd_bus_send(bus,s,NULL)<0)goto done;
 result=0;
done:sd_bus_message_unref(s);return result;
}
static int manager_main(void) {
 sd_bus *bus=NULL;sd_bus_message *m=NULL,*reply=NULL;
 int endpoint=-1,anchor=-1,epidfd=-1,eexit=-1,started=0,complete=0,matches=0,subscribed=0;
 int64_t deadline=now_ms()+6500;char unit[96]={0};struct stat original={0};
 sd_id128_t id;if(getrandom(&id,sizeof id,0)!=(ssize_t)sizeof id)return 40;
 if(sd_bus_new(&bus)<0 || sd_bus_set_fd(bus,0,0)<0 || sd_bus_set_server(bus,1,id)<0 ||
    sd_bus_set_sender(bus,":1.0")<0 || sd_bus_negotiate_fds(bus,!is_case("no_fds"))<0 ||
    sd_bus_start(bus)<0)goto done;
 while(now_ms()>=0 && now_ms()<deadline && !complete) {
  int r=sd_bus_process(bus,&m);if(r<0)break;
  if(!r) {if(sd_bus_wait(bus,100000)<0)break;continue;}
  if(!m)continue;
  const char *method=sd_bus_message_get_member(m);
  if(!method)goto bad;
  if(sd_bus_message_is_method_call(m,FM_DBUS_IFACE,"Hello")) {
   if(sd_bus_reply_method_return(m,"s",":1.1")<0)goto bad;
  } else if(sd_bus_message_is_method_call(m,FM_DBUS_IFACE,"GetNameOwner")) {
   if(sd_bus_reply_method_return(m,"s",is_case("wrong_owner")?":1.9":":1.0")<0)goto bad;
  } else if(sd_bus_message_is_method_call(m,FM_DBUS_IFACE,"AddMatch")) {
   const char *rule;
   if(sd_bus_message_read(m,"s",&rule)<=0 || (strcmp(rule,FM_MATCH) && strcmp(rule,FM_OWNER_MATCH)) ||
      is_case("match_error"))goto error_reply;
   ++matches;
   if(sd_bus_reply_method_return(m,"")<0)goto bad;
  } else if(sd_bus_message_is_method_call(m,FM_IFACE,"Subscribe")) {
   if(matches!=2 || subscribed || is_case("subscribe_error"))goto error_reply;
   subscribed=1;
   if(is_case("early_job") && job_signal(bus,"none.service"))goto bad;
   if(sd_bus_reply_method_return(m,"")<0)goto bad;
  } else if(sd_bus_message_is_method_call(m,FM_IFACE,"StartTransientUnit")) {
   int borrowed=-1;
   if(!subscribed || started || parse_request(m,unit,&endpoint,&borrowed,&original))goto error_reply;
   if(sd_bus_message_new_method_return(m,&reply)<0)goto bad;
   m=sd_bus_message_unref(m);
   /* Borrowed message FD closes on unref; retained native duplicate remains. */
   errno=0;if(fcntl(borrowed,F_GETFD)!=-1 || errno!=EBADF)goto bad;
   anchor=fcntl(endpoint,F_DUPFD_CLOEXEC,3);
   if(!refs_match(endpoint,anchor,&original))goto bad;
   struct clone_args args={0};args.flags=CLONE_PIDFD;args.pidfd=(uint64_t)(uintptr_t)&epidfd;args.exit_signal=SIGCHLD;
   pid_t parent=getpid();long child=syscall(SYS_clone3,&args,sizeof args);
   started=epidfd>=0;
   if(child<0)goto bad;
   if(!child) {
    if(dup2(endpoint,0)!=0)_exit(20);
    _exit(e_probe(parent));
   }
   started=1;
   if(is_case("owner_changed") && owner_signal(bus))goto bad;
   if(job_signal(bus,unit) || (is_case("duplicate_job") && job_signal(bus,unit)))goto bad;
   if(is_case("start_timeout")) {reply=sd_bus_message_unref(reply);continue;}
   if(sd_bus_message_append(reply,is_case("wrong_reply_type")?"s":"o","/org/freedesktop/systemd1/job/1")<0 ||
      sd_bus_send(bus,reply,NULL)<0)goto bad;
   reply=sd_bus_message_unref(reply);
  } else if(sd_bus_message_is_method_call(m,FM_IFACE,"UnrefUnit")) {
   const char *arg;
   if(sd_bus_message_read(m,"s",&arg)<=0 || strcmp(arg,unit) || is_case("unref_error") || epidfd<0)goto error_reply;
   int owned=epidfd;epidfd=-1;
   int waited=reap_original(owned,&eexit);close_one(&owned);
   if(waited || eexit!=0){uncertain=1;goto bad;}
   if(!refs_match(endpoint,anchor,&original))goto bad;
   close_one(&endpoint);close_one(&anchor);
   if(is_case("late_duplicate") && job_signal(bus,unit))goto bad;
   if(is_case("late_owner_change") && owner_signal(bus))goto bad;
   if(uncertain || sd_bus_reply_method_return(m,"")<0)goto bad;
   if(is_case("duplicate_after_reply") && job_signal(bus,unit))goto bad;
   if(sd_bus_flush(bus)<0)goto bad;
   complete=1;
  } else goto error_reply;
  m=sd_bus_message_unref(m);continue;
error_reply:
  if(endpoint>=0 && epidfd<0) {close_one(&endpoint);close_one(&anchor);}
  if(sd_bus_reply_method_errorf(m,"org.freedesktop.systemd1.FixtureRejected","fixed fixture rejected")<0)goto bad;
  m=sd_bus_message_unref(m);continue;
bad:break;
 }
done:
 sd_bus_message_unref(m);sd_bus_message_unref(reply);
 sd_bus_close_unref(bus);
 if(epidfd>=0) {
  int owned=epidfd;epidfd=-1;
  if(reap_original(owned,&eexit))uncertain=1;
  close_one(&owned);
 }
 if(endpoint>=0 || anchor>=0) {
  if(refs_match(endpoint,anchor,&original)){close_one(&endpoint);close_one(&anchor);}
  else uncertain=1;
 }
 return complete && !uncertain?0:(started?41:40);
}
int fm_open_private_fixture(struct fm_link *l) {
 int pair[2]={-1,-1};
 if(socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0,pair))return -1;
 l->fd=pair[0];
 l->anchor=fcntl(l->fd,F_DUPFD_CLOEXEC,3);
 if(l->anchor<0 || fstat(l->fd,&l->original)){close_one(&pair[1]);return -1;}
 struct clone_args args={0};args.flags=CLONE_PIDFD;args.pidfd=(uint64_t)(uintptr_t)&l->pidfd;args.exit_signal=SIGCHLD;
 long child=syscall(SYS_clone3,&args,sizeof args);
 if(child<0){close_one(&pair[1]);return -1;}
 if(!child) {
  if(dup2(pair[1],0)!=0 || syscall(SYS_close_range,3u,~0u,0u))_exit(40);
  _exit(manager_main());
 }
 close_one(&pair[1]);
 if(uncertain || sd_bus_new(&l->bus)<0 || sd_bus_set_fd(l->bus,l->fd,l->fd)<0)return -1;
 l->bus_owns_fd=1; /* ownership changes only after successful set_fd */
 if(sd_bus_set_bus_client(l->bus,1)<0 ||
    sd_bus_set_allow_interactive_authorization(l->bus,0)<0 ||
    sd_bus_negotiate_fds(l->bus,1)<0 || sd_bus_start(l->bus)<0)return -1;
 return 0;
}
