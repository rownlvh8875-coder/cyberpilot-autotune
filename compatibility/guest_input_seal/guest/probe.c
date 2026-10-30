/* FIXED HARMLESS SOFTWARE GUEST ONLY. Never run this ELF on the host. */
#define _GNU_SOURCE
#include "../../guest_consumption/guest/sha256.h"
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <time.h>
#include <unistd.h>

#define SCOPE "guest-input-seal-v1: fixed software guest only\n"
#define FULL 15
#define FUTURE 23
static const char input[]="0123456789ABCDEF\n";
static uint64_t sequence;

static void require(int ok) { if(!ok) _exit(2); }
static uint64_t mono(void)
{
  struct timespec t;require(clock_gettime(CLOCK_MONOTONIC,&t)==0);
  return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;
}
static void begin(const char *kind,const char *label)
{
  printf("SEAL {\"seq\":%"PRIu64",\"time_ns\":%"PRIu64",\"kind\":\"%s\",\"label\":\"%s\",\"values\":[",sequence++,mono(),kind,label);
}
static void end(void) { puts("]}");require(!ferror(stdout)); }
/* These are libc results and errno, NOT kernel raw negative returns. */
static void operation(const char *label,long result)
{
  int saved=result<0?errno:0;
  begin("OP",label);printf("%ld,%d",result,saved);end();
}
static void snapshot(const char *label,int fd)
{
  struct stat info,after;char hash[65];unsigned char data[64];
  require(fstat(fd,&info)==0 && S_ISREG(info.st_mode) && info.st_size==17);
  ssize_t count=pread(fd,data,sizeof(data),0);require(count==17);
  struct sha256_ctx ctx;sha256_init(&ctx);sha256_update(&ctx,data,(size_t)count);sha256_final(&ctx,hash);
  require(fstat(fd,&after)==0 && info.st_dev==after.st_dev && info.st_ino==after.st_ino && info.st_size==after.st_size);
  errno=0;int seals=fcntl(fd,F_GET_SEALS),saved=seals<0?errno:0;
  begin("SNAP",label);printf("%"PRIu64",%"PRIu64",%"PRIu64",\"%s\",",(uint64_t)info.st_dev,(uint64_t)info.st_ino,(uint64_t)count,hash);
  if(seals<0)printf("null");else printf("%d",seals);
  printf(",%d,%u",saved,(unsigned)(info.st_mode&07777));end();
}
static int new_memfd(void)
{
  /* MFD_NOEXEC_SEAL=8. No MFD_EXEC fallback; F_SEAL_EXEC is mode context. */
  int fd=(int)syscall(SYS_memfd_create,"fixed-input",1|2|8);require(fd>=0);
  require(write(fd,input,17)==17);return fd;
}
static void seal(const char *label,int fd,int mask)
{ errno=0;operation(label,fcntl(fd,F_ADD_SEALS,mask)); }
static void write_byte(const char *label,int fd)
{ errno=0;operation(label,pwrite(fd,"X",1,0)); }
static void map_denial(int fd)
{
  errno=0;void *p=mmap(NULL,4096,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);int saved=errno;
  if(p!=MAP_FAILED){require(munmap(p,4096)==0);errno=0;operation("map_shared",0);}
  else {errno=saved;operation("map_shared",-1);}
}
static void local(const char *label,volatile unsigned char *p)
{ *p='X';begin("LOCAL",label);printf("%u",(unsigned)*p);end(); }
static void bind_read(int expected,int actual)
{
  /* Pin expected and actual through read. FD0 is an actual reused descriptor. */
  require(dup2(actual,0)==0);
  struct stat want,got;require(fstat(expected,&want)==0 && fstat(0,&got)==0);
  begin("BIND","read");printf("%"PRIu64",%"PRIu64",%"PRIu64",%"PRIu64",0",(uint64_t)want.st_dev,(uint64_t)want.st_ino,(uint64_t)got.st_dev,(uint64_t)got.st_ino);end();
  snapshot("read",0);
}
static int guest_guard(void)
{
  struct utsname u;char text[128];
  if(uname(&u)||strcmp(u.release,"6.12.113+deb13-cloud-amd64")||strcmp(u.machine,"x86_64")||geteuid()!=0)return -1;
  int fd=open("/etc/guest-input-seal-scope",O_RDONLY|O_CLOEXEC);if(fd<0)return -1;
  ssize_t n=read(fd,text,sizeof(text));close(fd);
  return n==(ssize_t)strlen(SCOPE)&&!memcmp(text,SCOPE,(size_t)n)?0:-1;
}
int main(int argc,char **argv)
{
  if(argc!=2||strlen(argv[1])!=4||memcmp(argv[1],"IS0",3)||argv[1][3]<'1'||argv[1][3]>'8'||guest_guard()||sha256_selfcheck())return 2;
  setvbuf(stdout,NULL,_IOLBF,0);umask(022);
  const char *selected=argv[1];int which=selected[3]-'0';
  int fd=which==5?open("/lab/chmod-input",O_RDWR|O_CLOEXEC):new_memfd();require(fd>=0);
  begin("BEGIN",selected);printf("\"guest-input-seal-v1\"");end();snapshot("before",fd);
  if(which==1){
    int alias=dup(fd);require(alias>=0);char path[64];snprintf(path,sizeof(path),"/proc/self/fd/%d",fd);
    int reopened=open(path,O_RDWR|O_CLOEXEC);require(reopened>=0);
    struct stat a,b;require(fstat(fd,&a)==0 && fstat(alias,&b)==0 && a.st_dev==b.st_dev && a.st_ino==b.st_ino);
    require(fstat(reopened,&b)==0 && a.st_dev==b.st_dev && a.st_ino==b.st_ino);
    seal("seal1",fd,FULL);snapshot("sealed",fd);
    write_byte("write_original",fd);write_byte("write_dup",alias);write_byte("write_reopen",reopened);
    errno=0;operation("shrink",ftruncate(fd,16));errno=0;operation("grow",ftruncate(fd,18));map_denial(fd);
    snapshot("after",fd);bind_read(fd,fd);close(alias);close(reopened);
  }else if(which==2||which==3||which==8){
    int prot=which==8?PROT_READ:PROT_READ|PROT_WRITE;
    volatile unsigned char *p=mmap(NULL,4096,prot,MAP_SHARED,fd,0);require(p!=MAP_FAILED);
    seal(which==3?"seal_future":"seal1",fd,which==3?FUTURE:FULL);
    snapshot(which==3?"future":"failed",fd);
    if(which!=8){local("shared",p);snapshot("mutated",fd);}
    if(which==3){write_byte("write_original",fd);map_denial(fd);bind_read(fd,fd);require(munmap((void *)p,4096)==0);}
    else {
      errno=0;operation("unmap",munmap((void *)p,4096));
      if(which==2){errno=0;operation("restore",pwrite(fd,input,17,0));}
      seal("seal2",fd,FULL);snapshot("sealed",fd);bind_read(fd,fd);
    }
  }else if(which==4){
    seal("seal1",fd,FULL);snapshot("sealed",fd);int other=new_memfd();
    seal("seal_other",other,FULL);snapshot("other",other);
    require(dup2(fd,0)==0);bind_read(fd,other);close(other);
  }else if(which==5){
    errno=0;operation("chmod",fchmod(fd,0444));snapshot("chmod",fd);
    require(setgroups(0,NULL)==0 && setgid(65534)==0 && setuid(65534)==0 && prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0);
    begin("CRED","write");printf("%u,%u,%d",(unsigned)geteuid(),(unsigned)getegid(),prctl(PR_GET_NO_NEW_PRIVS,0,0,0,0));end();
    write_byte("write_original",fd);snapshot("mutated",fd);bind_read(fd,fd);
  }else if(which==6){
    seal("seal1",fd,FULL);snapshot("sealed",fd);
    int other=open("/lab/replacement",O_RDWR|O_CREAT|O_EXCL|O_CLOEXEC,0644);require(other>=0);
    require(write(other,"X123456789ABCDEF\n",17)==17);
    errno=0;operation("replace",rename("/lab/replacement","/lab/chmod-input"));
    int reopened=open("/lab/chmod-input",O_RDONLY|O_CLOEXEC);require(reopened>=0);
    snapshot("replacement",reopened);bind_read(fd,reopened);snapshot("after",fd);close(other);close(reopened);
  }else if(which==7){
    seal("seal1",fd,FULL);snapshot("sealed",fd);
    volatile unsigned char *p=mmap(NULL,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE,fd,0);require(p!=MAP_FAILED);
    local("private",p);snapshot("after",fd);bind_read(fd,fd);require(munmap((void *)p,4096)==0);
  }
  begin("END",selected);end();close(fd);close(0);return 0;
}
