/* Fixed E entry; no callback/path/command/resource-recovery interface. */
#define main ci_entry_reference_main
#include "../worker_entry/integration.c"
#undef main
int ci_peer_fixed(void) {
 pid_t manager=getppid();
 int null=open("/dev/null",O_RDWR|O_NOFOLLOW|O_CLOEXEC);
 if(manager<=1 || null<0 || dup2(null,1)!=1 || dup2(null,2)!=2 ||
    syscall(SYS_close_range,3u,~0u,0u) || getppid()!=manager)return 40;
 return entry_peer();
}
