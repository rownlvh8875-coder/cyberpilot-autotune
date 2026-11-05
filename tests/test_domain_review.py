"""Review regressions: fixed private native fixtures, no real cgroup writes."""

import subprocess

import pytest

from native_e_lab.domain import _binary


@pytest.mark.parametrize(
    "case", ["identity_unknown", "enumeration_error", "normal_exit137", "sigkill"]
)
def test_native_domain_review_failures(tmp_path, case):
    native = _binary().with_suffix(".c")
    text = native.read_text()
    copied = tmp_path / "instrumented.c"
    copied.write_text(
        text.replace(
            "int main(int argc, char **argv)", "int unused_domain_main(int argc, char **argv)"
        )
    )
    strict = "wait_domain_original" in text
    waitcall = "wait_domain_original(fd,&killed)" if strict else "wait_original(fd,&status)"
    if not strict:
        waitcall = "wait_original(fd,&status)"
    raw = r"""
#include "instrumented.c"
#include <stdarg.h>
#include <stddef.h>
"""
    wraps = []
    if case == "identity_unknown":
        raw += r"""
static int checks=0;
long __wrap_syscall(long n,...) {
 if(n!=SYS_kcmp){errno=ENOSYS;return -1;}
 if(++checks==2){errno=EIO;return -1;}return 0;
}
int main(int argc,char **argv) {
 if(argc!=2)return 2;
 int parent=open(argv[1],O_DIRECTORY|O_RDONLY);
 if(parent<0||mkdirat(parent,"D",0700))return 3;
 int d=openat(parent,"D",O_DIRECTORY|O_RDONLY),a=dup(d);
 if(!original_D(parent,d,a,"D"))return 4;
 if(original_D(parent,d,a,"D"))return 5;
 if(!uncertain)return 6;
 /* Even if a later query could succeed, unknown original binding is terminal. */
 if(original_D(parent,d,a,"D") || checks!=2)return 7;
 close(a);close(d);close(parent);return 0;
}
"""
        wraps = ["-Wl,--wrap=syscall"]
    elif case == "enumeration_error":
        raw += r"""
struct dirent *__wrap_readdir(DIR *dir) {
 (void)dir;static int count=0;static struct dirent e;
 if(count==5){errno=EIO;return NULL;}
 snprintf(e.d_name,sizeof e.d_name,"%d",count++);return &e;
}
int __real_stat(const char *,struct stat *);
int __wrap_stat(const char *p,struct stat *st) {
 if(strstr(p,"/fd/")){
  int n=atoi(strrchr(p,'/')+1);memset(st,0,sizeof *st);
  st->st_mode=n<=2?S_IFCHR:n==3?S_IFSOCK:S_IFREG;st->st_dev=1;st->st_ino=2;return 0;
 }return __real_stat(p,st);
}
int main(void) {
 struct stat data={.st_dev=1,.st_ino=2};
 if(worker_fds(getpid(),&data))return 5;
 return uncertain?0:6;
}
"""
        wraps = ["-Wl,--wrap=readdir", "-Wl,--wrap=stat"]
    else:
        killed_case = case == "sigkill"
        raw += r"""
int main(void) {
 int fd=-1;struct clone_args args={0};
 args.flags=CLONE_PIDFD;args.pidfd=(uint64_t)(uintptr_t)&fd;args.exit_signal=SIGCHLD;
 long child=syscall(SYS_clone3,&args,sizeof args);
 if(child<0)return 2;
 if(!child){CHILD_BODY}
 PARENT_SIGNAL
 int status=-1,killed=-1;
 int result=WAIT_CALL;
 LEGACY_MAP
 close(fd);
 return result || killed!=EXPECTED ? 5:0;
}
"""
        raw = raw.replace(
            "CHILD_BODY", "alarm(2);pause();_exit(99);" if killed_case else "_exit(137);"
        )
        raw = raw.replace(
            "PARENT_SIGNAL",
            "if(syscall(SYS_pidfd_send_signal,fd,SIGKILL,NULL,0))return 3;" if killed_case else "",
        )
        raw = raw.replace("WAIT_CALL", waitcall)
        raw = raw.replace("LEGACY_MAP", "" if strict else "killed=(status==137);")
        raw = raw.replace("EXPECTED", "1" if killed_case else "0")
    src = tmp_path / "probe.c"
    src.write_text(raw)
    binary = tmp_path / "probe"
    r = subprocess.run(
        ["cc", "-std=c11", "-O0", "-I", str(native.parent), *wraps, "-o", str(binary), str(src)],
        capture_output=True,
    )
    assert r.returncode == 0, r.stderr
    r = subprocess.run(
        [str(binary), str(tmp_path)] if case == "identity_unknown" else [str(binary)],
        env={"LANG": "C.UTF-8"},
        cwd=tmp_path,
        capture_output=True,
        timeout=6,
    )
    assert r.returncode == 0, (case, r.returncode, r.stderr)
