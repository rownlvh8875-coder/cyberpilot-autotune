/* Fixed native real-cgroup lab adapter. NOT an administrator factory/provider. */
#pragma push_macro("main")
#undef main
#define main rl_old_cohort_main
#include "../cohort_integration/cohort.c"
#undef main
#pragma pop_macro("main")
extern int rl_open_current_parent(void);
static atomic_uint rl_attempted;
static int rl_acquire_parent(struct ci_parent *p) {
 p->fd=rl_open_current_parent();
 if(p->fd<0 || fstat(p->fd,&p->original))return -1;
 p->anchor=fcntl(p->fd,F_DUPFD_CLOEXEC,3);
 p->base=fcntl(p->fd,F_DUPFD_CLOEXEC,3);
 strcpy(p->leaf,".");
 return refs_match(p->fd,p->anchor,&p->original) &&
        refs_match(p->base,p->anchor,&p->original)?0:-1;
}
int rl_run_fixed(void) {
 if(atomic_exchange_explicit(&rl_attempted,1,memory_order_acq_rel)) {
  printf("{\"outcome\":\"ALREADY_ATTEMPTED\",\"cleanup\":\"UNKNOWN\","
   "\"start_attempts\":0,\"e_birth\":null,\"worker_started\":null,"
   "\"actual_manager\":false,\"native_unit_creation_calls\":0,"
   "\"custody_qualified\":false,\"credential_kernel_verified\":false,"
   "\"factory_adopted_e_pidfd\":false}\n");
  return 20;
 }
 uncertain=0;
 struct fm_link l={.fd=-1,.anchor=-1,.pidfd=-1};
 struct fm_observation o={0};sd_bus_slot *filter=NULL;
 sd_bus_message *request=NULL,*reply=NULL;
 struct channel control={.fd=-1,.anchor=-1};
 struct ci_parent parent={.base=-1,.fd=-1,.anchor=-1};int released=0;
 int pair[2]={-1,-1},complete=0,manager_exit=-1,opened=0;
 unsigned char random[16],ctx[CTX]={0};char unit[96]="cyberpilot-native-e-lab-";
 char job[128]={0};sd_id128_t generation={0},after={0};
 int64_t start=now_ms(),deadline=start+3500;
 if(geteuid()==0 || start<0)goto done;
 if(rl_acquire_parent(&parent))goto done;
 if(fm_open_private_fixture(&l))goto done;
 opened=1;
 if(!link_ok(&l) || sd_bus_is_bus_client(l.bus)<=0)goto done;
 while(sd_bus_is_ready(l.bus)<=0)if(pump(&l,deadline))goto done;
 if(sd_bus_can_send(l.bus,'h')<=0 || sd_bus_get_bus_id(l.bus,&generation)<0 ||
    sd_bus_add_filter(l.bus,&filter,observe_bus,&o)<0)goto done;
 if(simple(&l,FM_DBUS_IFACE,FM_DBUS_PATH,FM_DBUS_IFACE,"GetNameOwner",FM_DEST,deadline,&reply))goto done;
 const char *owner;
 if(!sd_bus_message_has_signature(reply,"s") ||
    sd_bus_message_read(reply,"s",&owner)<=0 || strcmp(owner,":1.0"))goto done;
 reply=sd_bus_message_unref(reply);
 if(empty_method(&l,FM_DBUS_IFACE,FM_DBUS_PATH,FM_DBUS_IFACE,"AddMatch",FM_MATCH,deadline) ||
    empty_method(&l,FM_DBUS_IFACE,FM_DBUS_PATH,FM_DBUS_IFACE,"AddMatch",FM_OWNER_MATCH,deadline) ||
    empty_method(&l,FM_DEST,FM_PATH,FM_IFACE,"Subscribe",NULL,deadline))goto done;
 if(o.bad || getrandom(random,sizeof random,0)!=(ssize_t)sizeof random)goto done;
 for(size_t i=0;i<sizeof random;++i)snprintf(unit+(sizeof "cyberpilot-native-e-lab-"-1)+i*2,3,"%02x",random[i]);
 strcat(unit,".service");
 if(socketpair(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC|SOCK_NONBLOCK,0,pair) ||
    fm_build_start(l.bus,&request,unit,pair[1]))goto done;
 ++o.starts; /* consume before possibly ambiguous send/call; never retry */
 if(call_message(&l,request,deadline,&reply))goto done;
 request=sd_bus_message_unref(request);close_one(&pair[1]);
 const char *returned_job;
 if(!sd_bus_message_has_signature(reply,"o") ||
    sd_bus_message_read(reply,"o",&returned_job)<=0 ||
    text_copy(job,sizeof job,returned_job))goto done;
 reply=sd_bus_message_unref(reply);
 while(o.jobs==0 && !o.bad)if(pump(&l,deadline))goto done;
 if(o.bad || o.jobs!=1 || o.job_id!=1 || strcmp(o.job,job) || strcmp(o.unit,unit) ||
    strcmp(o.result,"done") || strcmp(job,"/org/freedesktop/systemd1/job/1") ||
    sd_bus_get_bus_id(l.bus,&after)<0 || memcmp(&generation,&after,sizeof generation))goto done;
 int endpoint=pair[0];pair[0]=-1;
 if(channel_init(&control,endpoint))goto done;
 if(ci_exchange(&control,&parent,ctx))goto done;
 deadline=now_ms()+3500;
 /* Recheck queued late/duplicate/owner-change signals before releasing original ref. */
 for(int i=0;i<8;++i) {
  if(!link_ok(&l))goto done;
  int r=sd_bus_process(l.bus,NULL);if(r<0)goto done;if(!r)break;
 }
 if(o.bad || o.jobs!=1 ||
    empty_method(&l,FM_DEST,FM_PATH,FM_IFACE,"UnrefUnit",unit,deadline))goto done;
 if(o.bad || o.jobs!=1 || ci_reap_manager(&l.pidfd,&manager_exit) || manager_exit!=0)goto done;
 /* The PRIVATE fixture peer exits here. This is not an EOF requirement on a
  * real shared system bus. Reap original M, then drain all final queued events. */
 int disconnected=0;
 for(int i=0;i<64;++i) {
  if(sd_bus_is_open(l.bus)<=0){disconnected=1;break;}
  if(!link_ok(&l))goto done;
  int r=sd_bus_process(l.bus,NULL);
  if(o.bad || o.jobs!=1)goto done;
  if(r<0) {if(sd_bus_is_open(l.bus)<=0){disconnected=1;break;}goto done;}
  if(!r) {
   int64_t left=remaining_us(deadline);
   if(left<0 || sd_bus_wait(l.bus,(uint64_t)left)<0)goto done;
  }
 }
 if(!disconnected || o.bad || o.jobs!=1)goto done;
 complete=1;
done:
 channel_close(&control);
 close_one(&pair[0]);close_one(&pair[1]);
 sd_bus_message_unref(request);sd_bus_message_unref(reply);
 sd_bus_slot_unref(filter);
 if(l.bus) {
  if(link_ok(&l)) {
   l.bus=sd_bus_close_unref(l.bus);
   if(l.bus_owns_fd)l.fd=-1;else close_one(&l.fd);
   close_one(&l.anchor);
  } else {
   errno=0;
   if(l.bus_owns_fd && sd_bus_is_open(l.bus)<=0 && fcntl(l.fd,F_GETFD)==-1 && errno==EBADF) {
    /* Library consumed its own FD on disconnect. Do not close that number again.
     * The void library teardown result itself remains UNAVAILABLE in the report. */
    l.bus=sd_bus_unref(l.bus);l.fd=-1;close_one(&l.anchor);
   } else uncertain=1; /* don't let library close a reused foreign descriptor */
  }
 } else if(l.fd>=0 || l.anchor>=0) {
  if(refs_match(l.fd,l.anchor,&l.original)){close_one(&l.fd);close_one(&l.anchor);}
  else uncertain=1;
 }
 if(l.pidfd>=0)ci_reap_manager(&l.pidfd,&manager_exit);
 if(parent.fd>=0 || parent.anchor>=0 || parent.base>=0) {
  if(refs_match(parent.fd,parent.anchor,&parent.original) &&
     refs_match(parent.base,parent.anchor,&parent.original)) {
   close_one(&parent.fd);close_one(&parent.anchor);close_one(&parent.base);
   if(!uncertain)released=1;
  } else uncertain=1; /* unknown OFD: retain; never inode-only close */
 }
 int success=complete && manager_exit==0 && released && !uncertain;
 const char *birth=manager_exit==0 || (manager_exit>=41 && manager_exit<=43)?"true":
   (manager_exit==40 || !opened?"false":"null");
 const char *worker=manager_exit==0 || manager_exit==42?"true":
   (manager_exit==43 || !opened?"false":"null");
 const char *fact=success?"true":"null";
 printf("{\"outcome\":\"%s\",\"cleanup\":\"%s\",\"start_attempts\":%d,"
  "\"e_birth\":%s,\"worker_started\":%s,\"parent_released\":%s,"
  "\"kernel_domain_verified\":%s,\"manager_owned_e\":%s,\"explicit_e_shutdown\":%s,"
  "\"factory_adopted_e_pidfd\":false,\"library_close_result\":\"UNAVAILABLE\","
  "\"actual_manager\":false,\"native_unit_creation_calls\":0,\"custody_qualified\":false,"
  "\"credential_kernel_verified\":false}\n",
  success?"REAL_CGROUP_COHORT_COMPLETE":(opened?"REJECTED":"UNAVAILABLE"),
  success?"NATIVE_HANDLES_CONFIRMED_LIBRARY_UNAVAILABLE":"UNKNOWN",o.starts,birth,worker,
  released?"true":"false",fact,fact,fact);
 return success?0:20;
}
int main(void){return rl_run_fixed();}
