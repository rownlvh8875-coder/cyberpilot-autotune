/* Closed successor coordinator. Default has no host scope and no manager connection. */
#include "internal.h"
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>
extern int fm_run_fixed(void);
static atomic_uint attempted;
int fi_run_fixed(void) {
 if(atomic_exchange_explicit(&attempted,1,memory_order_acq_rel)) {
  puts("{\"outcome\":\"ALREADY_ATTEMPTED\",\"intent_created\":null,\"intent_durable\":null,\"manager_invoked\":false,\"native_release\":\"UNKNOWN\",\"actual_manager\":false,\"worker_started\":false}");
  return 20;
 }
 static struct fi_intent i;fi_init(&i);
 int admitted=!fi_begin(&i),manager=0,result=20;
 if(admitted && !fi_guard(&i)) {manager=1;result=fm_run_fixed();}
 else if(admitted)i.unknown=1;
 fi_finish(&i);
 int success=admitted && manager && result==0 && !i.unknown;
 const char *durable=i.durable?"true":(i.created!=0 || !strcmp(i.outcome,"DENIED_EXISTING_INTENT")?"null":"false");
 const char *outcome=success?"PRIVATE_FACTORY_WITH_DURABLE_INTENT":
  (admitted?"REJECTED_OR_UNKNOWN":i.outcome);
 printf("{\"outcome\":\"%s\",\"intent_created\":%s,\"intent_durable\":%s,"
  "\"manager_invoked\":%s,\"native_release\":\"%s\",\"actual_manager\":false,\"worker_started\":false}\n",
  outcome,i.created<0?"null":(i.created?"true":"false"),durable,
  manager?"true":"false",i.unknown?"UNKNOWN":(i.retained_anchor_slots?"PARTIAL_REFS_RETAINED":"NO_SCOPE"));
 return success?0:20;
}
#ifdef FI_STANDALONE
int main(int argc,char **argv) {(void)argv;return argc==1?fi_run_fixed():20;}
#endif
