/* Stopped-task procfs observation only; no retained target FD duplicates. */
#define _GNU_SOURCE
#include "collector.h"
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

static int compare(const void *left, const void *right)
{
  uint64_t a=((const struct fd_record *)left)->fd, b=((const struct fd_record *)right)->fd;
  return (a>b)-(a<b);
}

int snapshot_fds(pid_t tid, struct fd_record *records, size_t capacity)
{
  char directory[64];
  snprintf(directory,sizeof(directory),"/proc/%d/fd",tid);
  DIR *stream=opendir(directory);
  if (!stream) return -1;
  size_t count=0;
  int failure=0;
  for (;;) {
    errno=0;
    struct dirent *entry=readdir(stream);
    if (!entry) { if (errno) failure=errno; break; }
    if (entry->d_name[0]=='.') continue;
    char *end=NULL;
    unsigned long descriptor=strtoul(entry->d_name,&end,10);
    if (!end || *end || descriptor>=2147483648UL || count==capacity) { failure=EOVERFLOW; break; }
    struct stat object;
    if (fstatat(dirfd(stream),entry->d_name,&object,0)) { failure=errno; break; }
    char path[96], line[512];
    snprintf(path,sizeof(path),"/proc/%d/fdinfo/%lu",tid,descriptor);
    FILE *info=fopen(path,"r");
    if (!info) { failure=errno; break; }
    unsigned long long flags=0, mount_id=0;
    int have_flags=0, have_mount=0;
    while (fgets(line,sizeof(line),info)) {
      if (sscanf(line,"flags:\t%llo",&flags)==1) have_flags=1;
      if (sscanf(line,"mnt_id:\t%llu",&mount_id)==1) have_mount=1;
    }
    if (ferror(info)) failure=EIO;
    fclose(info);
    if (failure || !have_flags || !have_mount) { if (!failure) failure=ENODATA; break; }
    records[count++]=(struct fd_record){descriptor,flags,(uint64_t)object.st_dev,
        (uint64_t)object.st_ino,(uint64_t)object.st_mode,mount_id};
  }
  closedir(stream);
  if (failure) { errno=failure; return -1; }
  qsort(records,count,sizeof(*records),compare);
  return (int)count;
}
