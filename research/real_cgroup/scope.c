/* Build-pinned old mapping guards, never old launcher. Current namespace only. */
#include "scope_reference.c"
__attribute__((visibility("hidden"))) int rl_open_current_parent(void) {
 char path[2048];
 if(geteuid()==0 || membership(getpid(),path,sizeof path) || !factory_service(path))return -1;
 return open_parent(path);
}
