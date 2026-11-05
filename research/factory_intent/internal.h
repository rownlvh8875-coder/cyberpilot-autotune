#ifndef FI_INTERNAL_H
#define FI_INTERNAL_H
#include <sys/stat.h>
#include <stddef.h>
struct fi_ref {int fd,anchor;struct stat original;};
struct fi_scope {struct fi_ref base,root;};
struct fi_intent {
 struct fi_scope scope;struct fi_ref file;
 unsigned char record[64];
 int begun,created,durable,unknown,finished,retained_anchor_slots;
 const char *outcome;
};
__attribute__((visibility("hidden"))) int fi_capture_ref(struct fi_ref *,int);
__attribute__((visibility("hidden"))) int fi_open_scope(struct fi_scope *);
__attribute__((visibility("hidden"))) void fi_init(struct fi_intent *);
__attribute__((visibility("hidden"))) int fi_begin(struct fi_intent *);
__attribute__((visibility("hidden"))) int fi_guard(struct fi_intent *);
__attribute__((visibility("hidden"))) void fi_finish(struct fi_intent *);
__attribute__((visibility("hidden"))) int fi_run_fixed(void);
#endif
