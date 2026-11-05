/* Minimal public sd-bus ABI declarations, audited against systemd v255 sd-bus.h.
 * Existing libsystemd.so.0 is linked; no private structs/vtables/header installation.
 * This is not package authentication or a protected-loader qualification. */
#ifndef FM_SDBUS_ABI_H
#define FM_SDBUS_ABI_H
#include <stdint.h>
#include <stddef.h>
typedef struct sd_bus sd_bus;
typedef struct sd_bus_message sd_bus_message;
typedef struct sd_bus_slot sd_bus_slot;
typedef union {uint8_t bytes[16];uint64_t qwords[2];} sd_id128_t;
typedef struct {const char *name,*message;int _need_free;} sd_bus_error;
typedef int (*sd_bus_message_handler_t)(sd_bus_message *,void *,sd_bus_error *);
_Static_assert(sizeof(sd_id128_t)==16,"sd-id128 ABI");
int sd_bus_new(sd_bus **);
int sd_bus_set_fd(sd_bus *,int,int);
int sd_bus_set_bus_client(sd_bus *,int);
int sd_bus_is_bus_client(sd_bus *);
int sd_bus_set_server(sd_bus *,int,sd_id128_t);
int sd_bus_set_sender(sd_bus *,const char *);
int sd_bus_negotiate_fds(sd_bus *,int);
int sd_bus_can_send(sd_bus *,char);
int sd_bus_start(sd_bus *);
int sd_bus_is_ready(sd_bus *);
int sd_bus_get_bus_id(sd_bus *,sd_id128_t *);
int sd_bus_set_allow_interactive_authorization(sd_bus *,int);
int sd_bus_set_method_call_timeout(sd_bus *,uint64_t);
sd_bus *sd_bus_close_unref(sd_bus *);
sd_bus *sd_bus_unref(sd_bus *);
int sd_bus_is_open(sd_bus *);
int sd_bus_process(sd_bus *,sd_bus_message **);
int sd_bus_wait(sd_bus *,uint64_t);
int sd_bus_flush(sd_bus *);
int sd_bus_send(sd_bus *,sd_bus_message *,uint64_t *);
int sd_bus_call(sd_bus *,sd_bus_message *,uint64_t,sd_bus_error *,sd_bus_message **);
int sd_bus_add_filter(sd_bus *,sd_bus_slot **,sd_bus_message_handler_t,void *);
sd_bus_slot *sd_bus_slot_unref(sd_bus_slot *);
int sd_bus_message_new_method_call(sd_bus *,sd_bus_message **,const char *,const char *,const char *,const char *);
int sd_bus_message_new_method_return(sd_bus_message *,sd_bus_message **);
int sd_bus_message_new_signal(sd_bus *,sd_bus_message **,const char *,const char *,const char *);
int sd_bus_message_set_sender(sd_bus_message *,const char *);
int sd_bus_message_set_allow_interactive_authorization(sd_bus_message *,int);
int sd_bus_message_set_auto_start(sd_bus_message *,int);
sd_bus_message *sd_bus_message_unref(sd_bus_message *);
const char *sd_bus_message_get_member(sd_bus_message *);
const char *sd_bus_message_get_sender(sd_bus_message *);
const char *sd_bus_message_get_path(sd_bus_message *);
int sd_bus_message_is_method_call(sd_bus_message *,const char *,const char *);
int sd_bus_message_is_signal(sd_bus_message *,const char *,const char *);
int sd_bus_message_is_method_error(sd_bus_message *,const char *);
int sd_bus_message_has_signature(sd_bus_message *,const char *);
int sd_bus_message_at_end(sd_bus_message *,int);
int sd_bus_message_open_container(sd_bus_message *,char,const char *);
int sd_bus_message_close_container(sd_bus_message *);
int sd_bus_message_enter_container(sd_bus_message *,char,const char *);
int sd_bus_message_exit_container(sd_bus_message *);
int sd_bus_message_append_basic(sd_bus_message *,char,const void *);
int sd_bus_message_append(sd_bus_message *,const char *,...);
int sd_bus_message_read(sd_bus_message *,const char *,...);
int sd_bus_reply_method_return(sd_bus_message *,const char *,...);
int sd_bus_reply_method_errorf(sd_bus_message *,const char *,const char *,...);
#endif
