"""Test-only linker injections. Production binary has no fault-mode controls."""

import socket
import subprocess

import pytest

from native_e_lab.protocol import Context, Stage, read_frame, send_frame
from native_e_lab.runner import _binary

WRAPPERS = {
    "abnormal": (
        "pread",
        r"""
#include <unistd.h>
ssize_t __wrap_pread(int fd, void *p, size_t n, off_t o) {
 (void)fd;(void)p;(void)n;(void)o;return 0;
}""",
        20,
    ),
    "early": (
        "prctl",
        r"""
#include <sys/prctl.h>
#include <unistd.h>
int __real_prctl(int, ...);
int __wrap_prctl(int option, unsigned long a, unsigned long b, unsigned long c, unsigned long d) {
 if(option==PR_SET_PDEATHSIG) _exit(51);
 return __real_prctl(option,a,b,c,d);
}""",
        20,
    ),
    "timeout": (
        "pread",
        r"""
#include <unistd.h>
#include <time.h>
ssize_t __wrap_pread(int fd, void *p, size_t n, off_t o) {
 (void)fd;(void)p;(void)n;(void)o;
 struct timespec t={.tv_sec=4};nanosleep(&t,0);return 0;
}""",
        20,
    ),
    "wait_unknown": (
        "waitid",
        r"""
#define _GNU_SOURCE
#include <sys/wait.h>
#include <errno.h>
#include <unistd.h>
int __real_waitid(idtype_t,id_t,siginfo_t *,int);
int __wrap_waitid(idtype_t t,id_t id,siginfo_t *info,int opts) {
 static int called=0;
 if(called++) _exit(99);
 int r=__real_waitid(t,id,info,opts);
 if(r==0) {errno=EIO;return -1;}return r;
}""",
        21,
    ),
    "close_unknown": (
        "close",
        r"""
#include <unistd.h>
#include <errno.h>
int __real_close(int);
int __wrap_close(int fd) {
 static int called=0;
 int r=__real_close(fd);
 if(fd==6) {if(called++) _exit(99);errno=EIO;return -1;}
 return r;
}""",
        21,
    ),
}


@pytest.mark.parametrize("case", WRAPPERS)
def test_native_failures_are_not_clean_success_and_no_wait_retry(tmp_path, case):
    symbol, raw, expected = WRAPPERS[case]
    wrapper = tmp_path / "inject.c"
    wrapper.write_text(raw)
    binary = tmp_path / "fixed-test-supervisor"
    src = _binary().with_suffix(".c")
    built = subprocess.run(
        [
            "cc",
            "-std=c11",
            "-D_GNU_SOURCE",
            "-O0",
            "-Wl,--wrap=" + symbol,
            "-o",
            str(binary),
            str(src),
            str(wrapper),
        ],
        capture_output=True,
    )
    assert built.returncode == 0, built.stderr
    a, b = socket.socketpair()
    child = subprocess.Popen(
        [str(binary)],
        stdin=b,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        close_fds=True,
        env={"LANG": "C.UTF-8"},
    )
    b.close()
    a.settimeout(6)
    ctx = Context.fresh()
    try:
        send_frame(a, ctx.message(Stage.BIND, 0))
        ctx.check(read_frame(a), Stage.OWNED, 1)
        send_frame(a, ctx.message(Stage.RUN, 2))
        a.shutdown(socket.SHUT_WR)
        assert child.wait(timeout=8) == expected
        if expected == 20:
            assert read_frame(a) is None
    finally:
        a.close()
        if child.returncode is None:
            child.wait(timeout=8)
