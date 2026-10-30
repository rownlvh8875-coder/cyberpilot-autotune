/* SHA-256 content identity only. No MAC, signature or authority. */
#ifndef CONSUMPTION_SHA256_H
#define CONSUMPTION_SHA256_H
#include <stdint.h>
#include <string.h>

struct sha256_ctx { uint32_t h[8]; uint64_t length; unsigned used; unsigned char block[64]; };
static uint32_t rotr32(uint32_t v, unsigned n) { return (v>>n)|(v<<(32-n)); }
static void sha256_block(struct sha256_ctx *s, const unsigned char *p)
{
  static const uint32_t k[64]={
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
  uint32_t w[64];
  for (unsigned i=0;i<16;i++) w[i]=(uint32_t)p[i*4]<<24|(uint32_t)p[i*4+1]<<16|(uint32_t)p[i*4+2]<<8|p[i*4+3];
  for (unsigned i=16;i<64;i++) {
    uint32_t a=rotr32(w[i-15],7)^rotr32(w[i-15],18)^(w[i-15]>>3);
    uint32_t b=rotr32(w[i-2],17)^rotr32(w[i-2],19)^(w[i-2]>>10);
    w[i]=w[i-16]+a+w[i-7]+b;
  }
  uint32_t a=s->h[0],b=s->h[1],c=s->h[2],d=s->h[3],e=s->h[4],f=s->h[5],g=s->h[6],h=s->h[7];
  for (unsigned i=0;i<64;i++) {
    uint32_t t1=h+(rotr32(e,6)^rotr32(e,11)^rotr32(e,25))+((e&f)^(~e&g))+k[i]+w[i];
    uint32_t t2=(rotr32(a,2)^rotr32(a,13)^rotr32(a,22))+((a&b)^(a&c)^(b&c));
    h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
  }
  s->h[0]+=a;s->h[1]+=b;s->h[2]+=c;s->h[3]+=d;s->h[4]+=e;s->h[5]+=f;s->h[6]+=g;s->h[7]+=h;
}
static void sha256_init(struct sha256_ctx *s)
{
  *s=(struct sha256_ctx){.h={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}};
}
static void sha256_update(struct sha256_ctx *s, const void *data, size_t n)
{
  const unsigned char *p=data; s->length+=n;
  while (n) {
    unsigned take=(unsigned)(n<64-s->used?n:64-s->used);
    memcpy(s->block+s->used,p,take);s->used+=take;p+=take;n-=take;
    if (s->used==64) { sha256_block(s,s->block);s->used=0; }
  }
}
static void sha256_final(struct sha256_ctx *s, char hex[65])
{
  static const char digits[]="0123456789abcdef";
  uint64_t bits=s->length*8; unsigned char pad[128]={0x80};
  unsigned n=s->used<56?56-s->used:120-s->used;
  sha256_update(s,pad,n);
  for (unsigned i=0;i<8;i++) pad[i]=(unsigned char)(bits>>(56-i*8));
  sha256_update(s,pad,8);
  for (unsigned i=0;i<32;i++) { unsigned byte=(s->h[i/4]>>(24-(i%4)*8))&255;hex[i*2]=digits[byte>>4];hex[i*2+1]=digits[byte&15]; }
  hex[64]=0;
}
static int sha256_selfcheck(void)
{
  struct sha256_ctx s; char h[65];
  sha256_init(&s);sha256_final(&s,h);
  if (strcmp(h,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")) return -1;
  sha256_init(&s);sha256_update(&s,"a",1);sha256_update(&s,"bc",2);sha256_final(&s,h);
  return strcmp(h,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");
}
#endif
