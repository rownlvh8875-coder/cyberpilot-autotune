#define main unused_direct_main
#include "supervisor.c"
#undef main
#include <sys/stat.h>
int main(int argc, char **argv) {
  (void)argv;
  if (argc != 1 || geteuid() == 0) return 22;
  struct stat st;
  if (fstat(3, &st) || !S_ISSOCK(st.st_mode) ||
      fstat(4, &st) || !S_ISREG(st.st_mode) || fcntl(4, F_GET_SEALS) != 15) return 31;
  if (write_all(3, "R", 1)) return 34;
  unsigned char go;
  if (exact(3, &go, 1, 0, now_ms() + 2000) || go != 'G') return 35;
  char actual[sizeof fixture];
  if (pread(4, actual, sizeof fixture - 1, 0) != (ssize_t)(sizeof fixture - 1) ||
      memcmp(actual, fixture, sizeof fixture - 1)) return 36;
  if (write_all(3, "D", 1)) return 37;
  poll(NULL, 0, 3500);
  return 42;
}
