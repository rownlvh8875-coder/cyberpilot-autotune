#ifndef FM_INTERNAL_H
#define FM_INTERNAL_H
#include "sdbus_abi.h"
#include <sys/stat.h>
#define FM_PATH "/org/freedesktop/systemd1"
#define FM_IFACE "org.freedesktop.systemd1.Manager"
#define FM_DEST "org.freedesktop.systemd1"
#define FM_DBUS_PATH "/org/freedesktop/DBus"
#define FM_DBUS_IFACE "org.freedesktop.DBus"
#define FM_MATCH "type='signal',interface='org.freedesktop.systemd1.Manager',member='JobRemoved'"
#define FM_OWNER_MATCH "type='signal',interface='org.freedesktop.DBus',member='NameOwnerChanged',arg0='org.freedesktop.systemd1'"
/* Internal factory output only. No API accepts a caller-built/serialized link. */
struct fm_link {sd_bus *bus;int fd,anchor,pidfd,bus_owns_fd;struct stat original;};
int fm_open_private_fixture(struct fm_link *);
int fm_build_start(sd_bus *,sd_bus_message **,const char *,int);
int fm_run_fixed(void);
#endif
