/* Fixed static x86_64 ELF synthetic worker. No libc/loader, arbitrary payload,
 * file/command inputs, inherited host directory or authority-recovery API.
 * Trusted-code self witness, NOT attestation against a malicious trampoline. */
#define _GNU_SOURCE
#include <stdint.h>
#include <stddef.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <poll.h>
#include <time.h>
#include <unistd.h>
#if !defined(__x86_64__) || defined(__ILP32__) || __SIZEOF_LONG__ != 8
#error "static fixed worker requires x86_64 LP64"
#endif
#define C 50
static long sc(long n,unsigned long a,unsigned long b,unsigned long c,
               unsigned long d,unsigned long e,unsigned long f) {
  register unsigned long r10 __asm__("r10")=d,r8 __asm__("r8")=e,r9 __asm__("r9")=f;
  long r;
  __asm__ volatile("syscall":"=a"(r):"a"(n),"D"(a),"S"(b),"d"(c),
                   "r"(r10),"r"(r8),"r"(r9):"rcx","r11","memory");
  return r;
}
#define S(n,a,b,c,d,e,f) sc(n,(unsigned long)(a),(unsigned long)(b),(unsigned long)(c), \
 (unsigned long)(d),(unsigned long)(e),(unsigned long)(f))
static void cp(void *d,const void *s,size_t n) {
  unsigned char *x=d;const unsigned char *y=s;while(n--)*x++=*y++;
}
static int eq(const void *a,const void *b,size_t n) {
  const unsigned char *x=a,*y=b;while(n--)if(*x++!=*y++)return 0;return 1;
}
static void zero(void *d,size_t n) {unsigned char *x=d;while(n--)*x++=0;}
static uint32_t get32(const unsigned char *p) {
 return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];
}
static void put32(unsigned char *p,uint32_t n) {
 for(int i=3;i>=0;--i){p[i]=(unsigned char)n;n>>=8;}
}
static void put64(unsigned char *p,uint64_t n) {
 for(int i=7;i>=0;--i){p[i]=(unsigned char)n;n>>=8;}
}
static int64_t ms(void) {
 struct timespec t;if(S(SYS_clock_gettime,CLOCK_MONOTONIC,&t,0,0,0,0))return -1;
 return (int64_t)t.tv_sec*1000+t.tv_nsec/1000000;
}
static int64_t deadline;
static int ready(short events) {
 int64_t current=ms();if(current<0)return -1;
 int64_t left=deadline-current;if(left<=0 || left>2500)return -1;
 struct pollfd p={3,events,0};return S(SYS_poll,&p,1,left,0,0,0)==1?0:-1;
}
static long receive(void *data,size_t n) {
 if(ready(POLLIN))return -1;
 struct iovec io={data,n};struct msghdr m;zero(&m,sizeof m);
 union {struct cmsghdr h;unsigned char b[CMSG_SPACE(8*sizeof(int))];} control;
 m.msg_iov=&io;m.msg_iovlen=1;m.msg_control=control.b;m.msg_controllen=sizeof control;
 long got=S(SYS_recvmsg,3,&m,MSG_CMSG_CLOEXEC|MSG_DONTWAIT,0,0,0);
 if(got<0)return -1;
 int bad=(m.msg_flags&(MSG_TRUNC|MSG_CTRUNC))!=0;
 for(struct cmsghdr *h=CMSG_FIRSTHDR(&m);h;h=CMSG_NXTHDR(&m,h)) {
  bad=1;
  if(h->cmsg_level==SOL_SOCKET && h->cmsg_type==SCM_RIGHTS && h->cmsg_len>=CMSG_LEN(0)) {
   size_t bytes=h->cmsg_len-CMSG_LEN(0);
   for(size_t i=0;i<bytes/sizeof(int);++i) {
    int fd;cp(&fd,(char *)CMSG_DATA(h)+i*sizeof(int),sizeof fd);
    (void)S(SYS_close,fd,0,0,0,0,0); /* consume received refs once; reject regardless */
   }
  }
 }
 return bad?-1:got;
}
static int read_exact(void *data,size_t n) {
 size_t used=0;while(used<n) {
  long r=receive((char *)data+used,n-used);if(r<=0)return -1;used+=(size_t)r;
 }return 0;
}
static int read_frame(unsigned char *b,size_t expected) {
 unsigned char n[4];if(read_exact(n,4) || get32(n)!=expected)return -1;
 return read_exact(b,expected);
}
static int send_frame(const unsigned char *b,size_t n) {
 unsigned char packet[132];if(n>128 || ready(POLLOUT))return -1;
 put32(packet,(uint32_t)n);cp(packet+4,b,n);
 return S(SYS_sendto,3,packet,n+4,MSG_NOSIGNAL|MSG_DONTWAIT,0,0)==(long)n+4?0:-1;
}
static void context(unsigned char *out,const unsigned char *ctx,int stage,int seq) {
 cp(out,ctx,C);out[5]=(unsigned char)stage;put32(out+6,(uint32_t)seq);
}
static int end(void) {unsigned char b;return receive(&b,1)==0?0:-1;}
struct dent {uint64_t ino;int64_t off;unsigned short len;unsigned char type;char name[];};
static int fd_entry(void) {
 for(int fd=0;fd<4;++fd) {
  struct stat st;
  if(S(SYS_fstat,fd,&st,0,0,0,0))return -1;
  if(fd<3) {
   if(!S_ISCHR(st.st_mode) || st.st_rdev!=259)return -1; /* Linux makedev(1,3) */
  } else if(!S_ISSOCK(st.st_mode))return -1;
 }
 long d=S(SYS_openat,AT_FDCWD,"/proc/self/fd",O_RDONLY|O_DIRECTORY|O_CLOEXEC,0,0,0);
 if(d<0)return -1;
 unsigned mask=0;int bad=d!=4;char buf[2048];
 for(;;) {
  long n=S(SYS_getdents64,d,buf,sizeof buf,0,0,0);if(n<0){bad=1;break;}if(!n)break;
  size_t off=0;while(off<(size_t)n) {
   struct dent *x=(struct dent *)(buf+off);
   if((size_t)n-off<20 || x->len<20 || x->len>(size_t)n-off){bad=1;break;}
   if(x->name[0]>='0' && x->name[0]<='9') {
    unsigned v=0;size_t k=0;
    while(k<x->len-19u && x->name[k]>='0' && x->name[k]<='9') {
     v=v*10+(unsigned)(x->name[k++]-'0');if(v>4){bad=1;break;}
    }
    if(k>=x->len-19u || x->name[k] || v>4)bad=1;else mask|=1u<<v;
   }
   off+=x->len;
  }
  if(bad)break;
 }
 if(S(SYS_close,d,0,0,0,0,0))bad=1;
 return bad || mask!=31?-1:0; /* 0..3 entry + self probe4, then probe closed */
}
int worker_main(void) {
 int64_t start=ms();if(start<0)return 70;
 deadline=start+2500;
 unsigned char ctx[C],b[82],expected[C];
 if(fd_entry() || read_frame(b,C+4) || !eq(b,"NWE1\1\1\0\0\0\0",10))return 70;
 cp(ctx,b,C);
 long parent=S(SYS_getppid,0,0,0,0,0,0);
 if(parent<=1 || get32(b+C)!=(uint32_t)parent)return 70;
 long fd=S(SYS_openat,AT_FDCWD,"/proc/self/exe",O_RDONLY|O_CLOEXEC,0,0,0);
 struct stat st;
 if(fd!=4 || S(SYS_fstat,fd,&st,0,0,0,0) || S(SYS_close,fd,0,0,0,0,0))return 70;
 context(b,ctx,2,1);put64(b+C,st.st_dev);put64(b+C+8,st.st_ino);
 put32(b+C+16,(uint32_t)parent);put32(b+C+20,(uint32_t)S(SYS_getuid,0,0,0,0,0,0));
 put32(b+C+24,(uint32_t)S(SYS_getgid,0,0,0,0,0,0));put32(b+C+28,15);
 if(send_frame(b,sizeof b) || read_frame(b,C))return 70;
 context(expected,ctx,3,2);if(!eq(b,expected,C) || end())return 70;
 context(b,ctx,4,3);
 if(send_frame(b,C) || S(SYS_shutdown,3,SHUT_WR,0,0,0,0) || S(SYS_close,3,0,0,0,0,0))return 70;
 return 0;
}
__asm__(".global _start\n_start:\nxor %rbp,%rbp\nand $-16,%rsp\ncall worker_main\n"
        "mov %eax,%edi\nmov $231,%eax\nsyscall\nud2\n");
