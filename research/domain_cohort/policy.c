/* Old launcher is build-renamed and NEVER called. Reuse actual old guards/wait. */
#include "domain_reference.c"
#include "internal.h"
#include <stdatomic.h>
static atomic_uint dr_attempted;
static int dr_bad(struct dr_domain *d) {d->phase=6;uncertain=1;return -1;}
static void dr_close(int *fd) {
 if(*fd<0)return;
 int owned=*fd;*fd=-1;
 close_once(owned);
}
static int dr_ofd(int fd,int anchor,const struct stat *st) {
 struct stat a,b;
 return fd>=0 && anchor>=0 && !fstat(fd,&a) && !fstat(anchor,&b) &&
  a.st_dev==st->st_dev && a.st_ino==st->st_ino && S_ISDIR(a.st_mode) &&
  b.st_dev==st->st_dev && b.st_ino==st->st_ino && S_ISDIR(b.st_mode) &&
  syscall(SYS_kcmp,getpid(),getpid(),0,(unsigned long)fd,(unsigned long)anchor)==0;
}
static int dr_original(struct dr_domain *d) {
 return dr_ofd(d->parent,d->parent_anchor,&d->parent_id) &&
  original_D(d->parent,d->fd,d->anchor,d->name);
}
int dr_create(struct dr_domain *d,int parent) {
 if(atomic_exchange_explicit(&dr_attempted,1,memory_order_acq_rel))return -1;
 memset(d,0,sizeof *d);d->parent=d->parent_anchor=d->fd=d->anchor=-1;
 d->phase=1;uncertain=0;
 struct statfs fs;char type[64];unsigned char nonce[16];
 d->parent=fcntl(parent,F_DUPFD_CLOEXEC,3);
 if(d->parent<0 || fstat(d->parent,&d->parent_id) || !S_ISDIR(d->parent_id.st_mode) ||
    d->parent_id.st_uid!=geteuid() || fstatfs(d->parent,&fs) ||
    fs.f_type!=CGROUP2_MAGIC || read_at_small(d->parent,"cgroup.type",type,sizeof type) ||
    strcmp(type,"domain\n") || uncertain)return dr_bad(d);
 d->parent_anchor=fcntl(d->parent,F_DUPFD_CLOEXEC,3);
 if(d->parent_anchor<0 || !dr_ofd(d->parent,d->parent_anchor,&d->parent_id) ||
    getrandom(nonce,sizeof nonce,0)!=(ssize_t)sizeof nonce)return dr_bad(d);
 strcpy(d->name,"owned-d-");
 for(unsigned i=0;i<sizeof nonce;++i)snprintf(d->name+8+i*2,3,"%02x",nonce[i]);
 if(mkdirat(d->parent,d->name,0700))return dr_bad(d);
 d->phase=2;
 d->fd=openat(d->parent,d->name,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 if(d->fd<0 || fstat(d->fd,&d->identity) ||
    (d->anchor=fcntl(d->fd,F_DUPFD_CLOEXEC,3))<0 ||
    !dr_original(d) || !no_descendants(d->fd))return dr_bad(d);
 return 0;
}
int dr_check(struct dr_domain *d,int child) {
 if((d->phase!=2 && d->phase!=3) || child<=0 || child==getpid() ||
    !dr_original(d) || !exactly_child(d->fd,child) || !no_descendants(d->fd))return dr_bad(d);
 d->phase=3;return 0;
}
int dr_stop(struct dr_domain *d,int child) {
 if(d->phase!=3 || d->stop_attempted || dr_check(d,child))return dr_bad(d);
 d->stop_attempted=1;d->phase=4; /* before possibly ambiguous open/write */
 int killfd=openat(d->fd,"cgroup.kill",O_WRONLY|O_NOFOLLOW|O_CLOEXEC);
 if(killfd<0)return dr_bad(d);
 ssize_t n=write(killfd,"1\n",2);dr_close(&killfd);
 return n==2 && !uncertain?0:dr_bad(d);
}
static int dr_empty(struct dr_domain *d) {
 char text[256];unsigned seen=0;
 if(read_at_small(d->fd,"cgroup.events",text,sizeof text))return 0;
 char *save=NULL;
 for(char *line=strtok_r(text,"\n",&save);line;line=strtok_r(NULL,"\n",&save)) {
  if(!strncmp(line,"populated ",10)) {
   if(seen++ || strcmp(line,"populated 0"))return 0;
  }
 }
 return seen==1 && !uncertain;
}
int dr_wait_reclaim(struct dr_domain *d,int *original) {
 if(d->phase!=4 || *original<0)return dr_bad(d);
 int owned=*original,killed=0;*original=-1;
 int result=wait_domain_original(owned,&killed);dr_close(&owned);
 if(result || !killed || uncertain || !dr_empty(d) || !dr_original(d))return dr_bad(d);
 if(unlinkat(d->parent,d->name,AT_REMOVEDIR))return dr_bad(d);
 d->removed=1;d->phase=5;return 0;
}
int dr_dispose(struct dr_domain *d) {
 if(d->fd>=0 || d->anchor>=0) {
  if(dr_ofd(d->fd,d->anchor,&d->identity)){dr_close(&d->fd);dr_close(&d->anchor);}
  else dr_bad(d);
 }
 if(d->parent>=0 || d->parent_anchor>=0) {
  if(dr_ofd(d->parent,d->parent_anchor,&d->parent_id)) {
   dr_close(&d->parent);dr_close(&d->parent_anchor);
  } else {
   /* No original OFD anchor established. Same inode is not custody.
    * Never close/recover that numeric FD; leave process-bound UNKNOWN. */
   dr_bad(d);
  }
 }
 return uncertain?-1:0;
}
