#include "internal.h"
#include <errno.h>
/* Default has no manager connection factory. No system/user/address fallback. */
int fm_open_private_fixture(struct fm_link *link) {(void)link;return -ENOSYS;}
