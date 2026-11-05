#include "internal.h"
#include <errno.h>
static int prop_begin(sd_bus_message *m,const char *name,const char *signature) {
 if(sd_bus_message_open_container(m,'r',"sv")<0 ||
    sd_bus_message_append_basic(m,'s',name)<0 ||
    sd_bus_message_open_container(m,'v',signature)<0)return -EINVAL;
 return 0;
}
static int prop_end(sd_bus_message *m) {
 return sd_bus_message_close_container(m)<0 || sd_bus_message_close_container(m)<0?-EINVAL:0;
}
static int prop_s(sd_bus_message *m,const char *name,const char *value) {
 return prop_begin(m,name,"s") || sd_bus_message_append_basic(m,'s',value)<0 || prop_end(m)?-EINVAL:0;
}
static int prop_b(sd_bus_message *m,const char *name,int value) {
 return prop_begin(m,name,"b") || sd_bus_message_append_basic(m,'b',&value)<0 || prop_end(m)?-EINVAL:0;
}
static int prop_t(sd_bus_message *m,const char *name,uint64_t value) {
 return prop_begin(m,name,"t") || sd_bus_message_append_basic(m,'t',&value)<0 || prop_end(m)?-EINVAL:0;
}
/* Internal fixed request encoder. Values are wire DATA only in this unbound stage.
 * Caller unit/endpoint come ONLY from fm_run_fixed's native creation, not public inputs.
 * No host binary, credential, resource limit or service is applied by this encoder. */
int fm_build_start(sd_bus *bus,sd_bus_message **out,const char *unit,int endpoint) {
 sd_bus_message *m=NULL;int r=-EINVAL;
 if(sd_bus_message_new_method_call(bus,&m,FM_DEST,FM_PATH,FM_IFACE,"StartTransientUnit")<0)goto done;
 if(sd_bus_message_set_auto_start(m,0)<0 || sd_bus_message_set_allow_interactive_authorization(m,0)<0 ||
    sd_bus_message_append_basic(m,'s',unit)<0 || sd_bus_message_append_basic(m,'s',"fail")<0 ||
    sd_bus_message_open_container(m,'a',"(sv)")<0)goto done;
 if(prop_s(m,"Type","exec") || prop_s(m,"User","cp-e-lab") || prop_s(m,"Group","cp-e-lab") ||
    prop_s(m,"Restart","no") || prop_s(m,"DelegateSubgroup",".supervisor") ||
    prop_b(m,"AddRef",1) || prop_b(m,"NoNewPrivileges",1) ||
    prop_t(m,"CapabilityBoundingSet",192) || prop_t(m,"AmbientCapabilities",192) ||
    prop_t(m,"RuntimeMaxUSec",30000000) || prop_t(m,"TimeoutStartUSec",5000000) ||
    prop_t(m,"TimeoutStopUSec",5000000) || prop_t(m,"MemoryMax",134217728) ||
    prop_t(m,"MemorySwapMax",0) || prop_t(m,"TasksMax",8) ||
    prop_t(m,"CPUQuotaPerSecUSec",250000))goto done;
 if(prop_begin(m,"DelegateControllers","as") ||
    sd_bus_message_append(m,"as",3,"cpu","memory","pids")<0 || prop_end(m))goto done;
 if(prop_begin(m,"ExecStart","a(sasb)") ||
    sd_bus_message_open_container(m,'a',"(sasb)")<0 ||
    sd_bus_message_append(m,"(sasb)","/usr/local/lib/cyberpilot-native-e-lab/e-bootstrap",1,
     "/usr/local/lib/cyberpilot-native-e-lab/e-bootstrap",0)<0 ||
    sd_bus_message_close_container(m)<0 || prop_end(m))goto done;
 if(prop_begin(m,"StandardInputFileDescriptor","h") ||
    sd_bus_message_append_basic(m,'h',&endpoint)<0 || prop_end(m) ||
    sd_bus_message_close_container(m)<0 ||
    sd_bus_message_open_container(m,'a',"(sa(sv))")<0 ||
    sd_bus_message_close_container(m)<0)goto done;
 *out=m;m=NULL;r=0;
done:
 sd_bus_message_unref(m);return r;
}
