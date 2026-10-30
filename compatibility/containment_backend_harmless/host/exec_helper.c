/* Single fixed harmless exec target. Not an arbitrary-command runner. */
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
int main(void)
{
  if (getuid() != 65534) return 2;
  int fd = open("/denied", O_RDONLY);
  int result = fd < 0 ? errno : 0;
  if (fd >= 0) close(fd);
  return write(STDOUT_FILENO, &result, sizeof(result)) == sizeof(result) ? 0 : 3;
}
