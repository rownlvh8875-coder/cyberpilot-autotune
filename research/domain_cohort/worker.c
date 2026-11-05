/* Fixed entry witness reused, followed by bounded stay-alive for stop proof. */
#define worker_main dr_entry_witness
#include "../worker_entry/fixed_worker.c"
#undef worker_main
int worker_main(void) {
 int result=dr_entry_witness();
 if(result)return result;
 /* No extra payload or FD; must be killed through the owned-domain stop path.
  * Natural expiry42 is distinguishable from exact SIGKILL. */
 (void)S(SYS_poll,0,0,4500,0,0,0);
 return 42;
}
