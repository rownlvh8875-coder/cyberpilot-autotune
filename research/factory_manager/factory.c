/* Native closed factory/lifecycle component. Default transport is UNAVAILABLE.
 * Only a separately linked TEST constructor creates a private synthetic manager.
 * No system bus/address/connect-by-name, privileged unit, E/W adoption or recovery. */
#pragma push_macro("main")
#undef main
#define main fm_reference_handoff_main
#include "../parent_handoff/handoff.c"
#undef main
#pragma pop_macro("main")
#include "internal.h"
#include <stdatomic.h>
static atomic_uint attempted;
struct fm_observation {
 int starts,jobs,bad;
 uint32_t job_id;
 char job[128],unit[96],result[24];
};
static int text_copy(char *out,size_t size,const char *text) {
 if(!text || strlen(text)>=size)return -1;
 strcpy(out,text);return 0;
}
static int observe_bus(sd_bus_message *m,void *data,sd_bus_error *error) {
 (void)error;struct fm_observation *o=data;
 if(sd_bus_message_is_signal(m,FM_IFACE,"JobRemoved")) {
  const char *path,*unit,*result;uint32_t id;
  ++o->jobs;
  const char *sender=sd_bus_message_get_sender(m),*object=sd_bus_message_get_path(m);
  if(o->jobs!=1 || o->starts!=1 || !sender || strcmp(sender,":1.0") ||
     !object || strcmp(object,FM_PATH) || !sd_bus_message_has_signature(m,"uoss") ||
     sd_bus_message_read(m,"uoss",&id,&path,&unit,&result)<=0 ||
     sd_bus_message_at_end(m,1)<=0 || text_copy(o->job,sizeof o->job,path) ||
     text_copy(o->unit,sizeof o->unit,unit) || text_copy(o->result,sizeof o->result,result))
    o->bad=1;
  else o->job_id=id;
  return 1; /* observation only; no spawning/grant/cleanup in callbacks */
 }
 if(sd_bus_message_is_signal(m,FM_DBUS_IFACE,"NameOwnerChanged")) {
  const char *name,*old,*next;
  if(sd_bus_message_read(m,"sss",&name,&old,&next)<=0 || !strcmp(name,FM_DEST))o->bad=1;
  return 1;
 }
 return 0;
}
static int link_ok(struct fm_link *l) {
 return l->bus && refs_match(l->fd,l->anchor,&l->original);
}
static int64_t remaining_us(int64_t deadline) {
 int64_t n=now_ms(),left=deadline-n;
 return n<0 || left<=0 || left>6500?-1:left*1000;
}
static int pump(struct fm_link *l,int64_t deadline) {
 if(!link_ok(l))return -1;
 int r=sd_bus_process(l->bus,NULL);
 if(r<0)return -1;
 if(r==0) {
  int64_t left=remaining_us(deadline);if(left<0)return -1;
  if(sd_bus_wait(l->bus,(uint64_t)left)<0)return -1;
 }
 return 0;
}
static int call_message(struct fm_link *l,sd_bus_message *m,int64_t deadline,sd_bus_message **reply) {
 int64_t left=remaining_us(deadline);
 if(!link_ok(l) || left<0)return -1;
 uint64_t timeout=(uint64_t)(left>800000?800000:left);
 return sd_bus_call(l->bus,m,timeout,NULL,reply)<0?-1:0;
}
static int simple(struct fm_link *l,const char *dest,const char *path,const char *iface,
 const char *method,const char *arg,int64_t deadline,sd_bus_message **reply) {
 sd_bus_message *m=NULL;int result=-1;
 if(sd_bus_message_new_method_call(l->bus,&m,dest,path,iface,method)<0)goto done;
 if(sd_bus_message_set_auto_start(m,0)<0 || sd_bus_message_set_allow_interactive_authorization(m,0)<0 ||
    (arg && sd_bus_message_append_basic(m,'s',arg)<0))goto done;
 result=call_message(l,m,deadline,reply);
done:
 sd_bus_message_unref(m);return result;
}
static int empty_method(struct fm_link *l,const char *dest,const char *path,const char *iface,
 const char *method,const char *arg,int64_t deadline) {
 sd_bus_message *reply=NULL;
 int result=simple(l,dest,path,iface,method,arg,deadline,&reply);
 if(!result && !sd_bus_message_has_signature(reply,""))result=-1;
 sd_bus_message_unref(reply);return result;
}
static int reap_once(int *handle,int *status) {
 int owned=*handle;*handle=-1; /* consume BEFORE an uncertain wait; never retry */
 int result=reap_original(owned,status);close_one(&owned);
 if(result)uncertain=1;
 return result;
}
int fm_run_fixed(void) {
 if(atomic_exchange_explicit(&attempted,1,memory_order_acq_rel)) {
  printf("{\"outcome\":\"ALREADY_ATTEMPTED\",\"cleanup\":\"UNKNOWN\","
   "\"start_attempts\":0,\"e_birth\":null,\"actual_manager\":false,"
   "\"actual_unit_created\":false,\"worker_started\":false}\n");
  return 20;
 }
 uncertain=0;
 struct fm_link l={.fd=-1,.anchor=-1,.pidfd=-1};
 struct fm_observation o={0};sd_bus_slot *filter=NULL;
 sd_bus_message *request=NULL,*reply=NULL;
 struct channel control={.fd=-1,.anchor=-1};struct frame f={0};
 int pair[2]={-1,-1},complete=0,manager_exit=-1,opened=0;
 unsigned char random[16],ctx[CTX]={0};char unit[96]="cyberpilot-native-e-lab-";
 char job[128]={0};sd_id128_t generation={0},after={0};
 int64_t start=now_ms(),deadline=start+3500;
 if(geteuid()==0 || start<0)goto done;
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
 memcpy(ctx,"FME1\1\1",6);write64(ctx+10,(uint64_t)start);
 if(getrandom(ctx+18,32,0)!=32 || send_stage(&control,ctx,1,0) ||
    read_frame(&control,&f,0) || !check_frame(&f,ctx,2,1,CTX) ||
    send_stage(&control,ctx,3,2) || shutdown(control.fd,SHUT_WR) ||
    read_frame(&control,&f,0) || !check_frame(&f,ctx,4,3,CTX) ||
    end_of_stream(&control))goto done;
 /* Recheck queued late/duplicate/owner-change signals before releasing original ref. */
 for(int i=0;i<8;++i) {
  if(!link_ok(&l))goto done;
  int r=sd_bus_process(l.bus,NULL);if(r<0)goto done;if(!r)break;
 }
 if(o.bad || o.jobs!=1 ||
    empty_method(&l,FM_DEST,FM_PATH,FM_IFACE,"UnrefUnit",unit,deadline))goto done;
 if(o.bad || o.jobs!=1 || reap_once(&l.pidfd,&manager_exit) || manager_exit!=0)goto done;
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
 frame_clear(&f);channel_close(&control);
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
 if(l.pidfd>=0)reap_once(&l.pidfd,&manager_exit);
 int success=complete && manager_exit==0 && !uncertain;
 const char *birth=manager_exit==0 || manager_exit==41?"true":(manager_exit==40 || !opened?"false":"null");
 printf("{\"outcome\":\"%s\",\"cleanup\":\"%s\",\"start_attempts\":%d,"
  "\"e_birth\":%s,\"e_parent_is_manager\":%s,\"factory_adopted_e_pidfd\":false,"
  "\"explicit_e_shutdown\":%s,\"manager_endpoint_retained\":%s,"
  "\"library_close_result\":\"UNAVAILABLE\",\"actual_manager\":false,\"actual_unit_created\":false,\"worker_started\":false}\n",
  success?"PRIVATE_MANAGER_PROTOCOL_COMPLETE":(opened?"REJECTED":"UNAVAILABLE"),
  success?"NATIVE_HANDLES_CONFIRMED_LIBRARY_UNAVAILABLE":"UNKNOWN",o.starts,birth,success?"true":"null",
  success?"true":"null",success?"true":"null");
 return success?0:20;
}
int main(void) {return fm_run_fixed();}
