/* Private native deny-only transaction. No receipt parsing/recovery/unlink API. */
#define _GNU_SOURCE
#include "internal.h"
#include <errno.h>
#include <fcntl.h>
#include <linux/kcmp.h>
#include <stdint.h>
#include <string.h>
#include <sys/random.h>
#include <sys/syscall.h>
#include <time.h>
#include <unistd.h>
static int eq(const struct stat *a,const struct stat *b) {
 return a->st_dev==b->st_dev && a->st_ino==b->st_ino &&
  (a->st_mode&S_IFMT)==(b->st_mode&S_IFMT);
}
static int ref_ok(const struct fi_ref *r) {
 struct stat a,b;
 return r->fd>=0 && r->anchor>=0 && !fstat(r->fd,&a) && !fstat(r->anchor,&b) &&
  eq(&a,&r->original) && eq(&a,&b) &&
  syscall(SYS_kcmp,getpid(),getpid(),KCMP_FILE,(unsigned long)r->fd,(unsigned long)r->anchor)==0;
}
int fi_capture_ref(struct fi_ref *r,int owned) {
 r->fd=owned;r->anchor=-1;
 if(owned<0 || fstat(owned,&r->original))return -1;
 r->anchor=fcntl(owned,F_DUPFD_CLOEXEC,3);
 return r->anchor<0 || !ref_ok(r)?-1:0;
}
void fi_init(struct fi_intent *i) {
 memset(i,0,sizeof *i);
 i->scope.base.fd=i->scope.base.anchor=i->scope.root.fd=i->scope.root.anchor=-1;
 i->file.fd=i->file.anchor=-1;i->outcome="UNAVAILABLE";
}
static int private_dir(const struct fi_ref *r) {
 struct stat s;
 return ref_ok(r) && !fstat(r->fd,&s) && S_ISDIR(s.st_mode) &&
  s.st_uid==geteuid() && s.st_gid==getegid() && (s.st_mode&07777)==0700;
}
static int scope_ok(struct fi_intent *i) {
 struct stat s;
 return private_dir(&i->scope.base) && private_dir(&i->scope.root) &&
  !fstatat(i->scope.base.fd,"state",&s,AT_SYMLINK_NOFOLLOW) &&
  eq(&s,&i->scope.root.original);
}
static int file_ok(struct fi_intent *i) {
 struct stat s,n;unsigned char bytes[64];
 return scope_ok(i) && ref_ok(&i->file) && !fstat(i->file.fd,&s) &&
  S_ISREG(s.st_mode) && s.st_uid==geteuid() && s.st_gid==getegid() &&
  (s.st_mode&07777)==0600 && s.st_nlink==1 && s.st_size==64 &&
  !fstatat(i->scope.root.fd,"attempt.intent",&n,AT_SYMLINK_NOFOLLOW) && eq(&s,&n) &&
  pread(i->file.fd,bytes,sizeof bytes,0)==(ssize_t)sizeof bytes &&
  !memcmp(bytes,i->record,sizeof bytes);
}
int fi_guard(struct fi_intent *i) {
 return i->begun && !i->finished && i->durable && !i->unknown && file_ok(i)?0:-1;
}
int fi_begin(struct fi_intent *i) {
 if(i->begun || i->finished)return -1;
 i->begun=1;
 if(geteuid()==0 || fi_open_scope(&i->scope))return -1;
 i->outcome="REJECTED_SCOPE";
 if(!scope_ok(i))return -1;
 struct timespec ts;
 if(clock_gettime(CLOCK_MONOTONIC,&ts) || ts.tv_sec<0 || ts.tv_nsec<0 || ts.tv_nsec>=1000000000 ||
  getrandom(i->record+16,32,0)!=32)return -1;
 memcpy(i->record,"NFI1\1",5);
 uint64_t seconds=(uint64_t)ts.tv_sec,nanos=(uint64_t)ts.tv_nsec;
 memcpy(i->record+48,&seconds,8);memcpy(i->record+56,&nanos,8);
 if(!scope_ok(i))return -1;
 i->outcome="UNKNOWN";i->created=-1;
 int fd=openat(i->scope.root.fd,"attempt.intent",
  O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC|O_NONBLOCK,0600);
 if(fd<0) {
  if(errno==EEXIST){i->created=0;i->outcome="DENIED_EXISTING_INTENT";}
  else i->unknown=1;
  return -1;
 }
 i->created=1;
 if(fi_capture_ref(&i->file,fd)) {i->unknown=1;return -1;}
 struct stat s;
 if(!scope_ok(i) || fstat(fd,&s) || !S_ISREG(s.st_mode) || s.st_uid!=geteuid() ||
  s.st_gid!=getegid() || (s.st_mode&07777)!=0600 || s.st_nlink!=1 || s.st_size!=0 ||
  write(fd,i->record,sizeof i->record)!=(ssize_t)sizeof i->record ||
  !file_ok(i) || fsync(fd) || !file_ok(i) || fsync(i->scope.root.fd) || !file_ok(i)) {
  i->unknown=1;return -1;
 }
 i->durable=1;i->outcome="DURABLE_INTENT";return 0;
}
static void release(struct fi_intent *i,struct fi_ref *r) {
 if(r->fd<0 && r->anchor<0)return;
 if(!ref_ok(r)){i->unknown=1;return;} /* no inode-only close after mapping loss */
 int a=r->fd;r->fd=-1; /* consume primary before uncertain close */
 if(close(a))i->unknown=1;
 /* No OFD comparator remains after consuming primary. Never close the final
  * anchor based on metadata alone, even when close(primary) returned success.
  * Terminal slots stay in the static process-bound intent; no later operation
  * may use/close/reconstruct them. Kernel process exit is a different fact. */
 ++i->retained_anchor_slots;
}
void fi_finish(struct fi_intent *i) {
 if(i->finished)return;
 if(i->durable && fi_guard(i))i->unknown=1;
 i->finished=1;
 release(i,&i->file);release(i,&i->scope.root);release(i,&i->scope.base);
}
