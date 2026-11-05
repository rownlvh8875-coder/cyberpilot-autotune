#include "internal.h"
#include <errno.h>
/* Future protected administrator scope NOT implemented. No lookup fallback. */
int fi_open_scope(struct fi_scope *scope) {(void)scope;return -ENOSYS;}
