"""Run actual one-shot kill-write block + cleanup tail on regular private fixtures."""

import subprocess

import pytest

from native_e_lab.domain import _binary


@pytest.mark.parametrize("fault", ["partial", "unknown_after_write"])
def test_domain_write_uncertainty_never_retries_or_unlinks(tmp_path, fault):
    native = _binary().with_suffix(".c")
    text = native.read_text()
    instrumented = tmp_path / "instrumented.c"
    instrumented.write_text(
        text.replace(
            "int main(int argc, char **argv)", "int unused_domain_main(int argc, char **argv)"
        )
    )
    start = text.index('  int killfd = openat(d, "cgroup.kill"')
    stop = text.index("  int killed;", start)
    tail = text[text.index("\ndone:", stop) :]
    actual_write_block = text[start:stop]
    prefix = r"""
#include "instrumented.c"
static int write_calls=0;
static void final_check(void) {if(write_calls!=1)_exit(99);}
ssize_t __real_write(int,const void *,size_t);
ssize_t __wrap_write(int fd,const void *data,size_t n) {
 (void)n;++write_calls;
 if(__real_write(fd,data,1)!=1)_exit(98);
 errno=EIO;
 return FAULT_RETURN;
}
int main(int argc,char **argv) {
 if(argc!=2)return 2;
 atexit(final_check);
 int parent=open(argv[1],O_DIRECTORY|O_RDONLY|O_CLOEXEC);
 if(parent<0 || mkdirat(parent,"D",0700))return 3;
 int d=openat(parent,"D",O_DIRECTORY|O_RDONLY|O_CLOEXEC),anchor=dup(d);
 int made=1,removed=0,wait_attempted=0,reaped=0,kill_attempted=0,result=20;
 int datafd=-1,pidfd=-1,pair[2]={-1,-1},workerfd=-1;
 pid_t child=-1;char name[]="D";
 int created=openat(d,"cgroup.kill",O_WRONLY|O_CREAT|O_EXCL|O_CLOEXEC,0600);
 if(created<0)return 4;close(created);
"""
    prefix = prefix.replace("FAULT_RETURN", "1" if fault == "partial" else "-1")
    probe = tmp_path / "probe.c"
    probe.write_text(prefix + actual_write_block + "\n  goto done;\n" + tail)
    binary = tmp_path / "probe"
    build = subprocess.run(
        [
            "cc",
            "-std=c11",
            "-O0",
            "-I",
            str(native.parent),
            "-Wl,--wrap=write",
            "-o",
            str(binary),
            str(probe),
        ],
        capture_output=True,
    )
    assert build.returncode == 0, build.stderr
    run = subprocess.run(
        [str(binary), str(tmp_path)],
        cwd=tmp_path,
        env={"LANG": "C.UTF-8"},
        capture_output=True,
        timeout=5,
    )
    assert run.returncode == 21, (run.returncode, run.stderr)
    assert (tmp_path / "D").is_dir()
    assert (tmp_path / "D/cgroup.kill").read_bytes() == b"1"
