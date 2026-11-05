/* PRIVATE build-only component interface, not provider/adoption API. */
#ifndef DR_INTERNAL_H
#define DR_INTERNAL_H
#include <sys/stat.h>
#define DR_PRIVATE __attribute__((visibility("hidden")))
struct dr_domain {
 int parent,parent_anchor,fd,anchor,phase,stop_attempted,removed;
 struct stat parent_id,identity;
 char name[48];
};
DR_PRIVATE int dr_create(struct dr_domain *,int); /* only live NPG1 P from fixed E */
DR_PRIVATE int dr_check(struct dr_domain *,int);
DR_PRIVATE int dr_stop(struct dr_domain *,int);
DR_PRIVATE int dr_wait_reclaim(struct dr_domain *,int *);
DR_PRIVATE int dr_dispose(struct dr_domain *);
#endif
