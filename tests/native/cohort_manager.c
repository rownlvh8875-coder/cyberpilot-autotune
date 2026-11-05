/* TEST ONLY. Original typed parser and signal encoders reused byte-for-byte. */
#define manager_main ci_reference_manager_main
#define fm_open_private_fixture ci_reference_open
#include "factory_fake_manager.c"
#undef fm_open_private_fixture
#undef manager_main
extern int ci_peer_fixed(void);
static int ci_wait_e(int owned,int *status) {
 struct pollfd p={owned,POLLIN,0};
 if(poll(&p,1,10000)!=1)uncertain=1;
 return reap_original(owned,status);
}
static int ci_manager_main(void) {
 sd_bus *bus=NULL;sd_bus_message *m=NULL,*reply=NULL;
 int endpoint=-1,anchor=-1,epidfd=-1,eexit=-1,started=0,complete=0,matches=0,subscribed=0;
 int64_t deadline=now_ms()+12000;char unit[96]={0};struct stat original={0};
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
   long child=syscall(SYS_clone3,&args,sizeof args);
   started=epidfd>=0;
   if(child<0)goto bad;
   if(!child) {
    if(dup2(endpoint,0)!=0)_exit(20);
    _exit(ci_peer_fixed());
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
   int waited=ci_wait_e(owned,&eexit);close_one(&owned);
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
  if(ci_wait_e(owned,&eexit))uncertain=1;
  close_one(&owned);
 }
 if(endpoint>=0 || anchor>=0) {
  if(refs_match(endpoint,anchor,&original)){close_one(&endpoint);close_one(&anchor);}
  else uncertain=1;
 }
 return complete && !uncertain?0:(started?(eexit==0 || eexit==41?42:(eexit==40?43:41)):40);
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
  _exit(ci_manager_main());
 }
 close_one(&pair[1]);
 if(uncertain || sd_bus_new(&l->bus)<0 || sd_bus_set_fd(l->bus,l->fd,l->fd)<0)return -1;
 l->bus_owns_fd=1; /* ownership changes only after successful set_fd */
 if(sd_bus_set_bus_client(l->bus,1)<0 ||
    sd_bus_set_allow_interactive_authorization(l->bus,0)<0 ||
    sd_bus_negotiate_fds(l->bus,1)<0 || sd_bus_start(l->bus)<0)return -1;
 return 0;
}
