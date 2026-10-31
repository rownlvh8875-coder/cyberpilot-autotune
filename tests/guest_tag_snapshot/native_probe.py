"""Opt-in controlled-layout scalar helper probe, not real kernel/LKMM proof."""

import subprocess
from pathlib import Path

from tests.guest_raw_lifetime.model import require


def probe(repo: Path, owned: Path) -> str:
    patch = (repo / "tests/guest_tag_snapshot/kernel.patch").read_text()
    section = patch.split("diff --git a/include/linux/cptagread.h b/include/linux/cptagread.h\n")
    require(len(section) == 2, "SNAPSHOT_HELPER_SOURCE_REQUIRED")
    header = "\n".join(
        s[1:] for s in section[1].splitlines() if s.startswith("+") and not s.startswith("+++")
    )
    source = (
        r"""
#include <stdint.h>
#include <stdbool.h>
#include <assert.h>
#include <stdio.h>
typedef uint64_t u64;
struct file {u64 cpl_cookie, cpl_scope; unsigned int cpb_epoch, cpb_origin;};
#define READ_ONCE(x) (*(volatile __typeof__(x) *)&(x))
"""
        + header
        + r"""
static struct cpt_snapshot sink;
static void emit_by_value(struct cpt_snapshot saved) { sink = saved; }
int main(void) {
  struct file f = {6, 0, 1, 1};
  struct cpt_snapshot saved = cpt_take(&f);
  f = (struct file){99, 88, 77, 2};
  emit_by_value(saved);
  saved.cookie = 123;
  assert(sink.cookie == 6 && sink.scope == 0 && sink.epoch == 1);
  assert(sink.origin == 1 && sink.captured);
  f = (struct file){0};
  saved = cpt_take(&f);
  assert(saved.captured && saved.cookie == 0 && saved.scope == 0);
  assert(saved.epoch == 0 && saved.origin == 0);
  puts("SAVED_SCALARS_PASS");
  return 0;
}
"""
    )
    path = owned / "scalar-probe.c"
    binary = owned / "scalar-probe"
    path.write_text(source)
    subprocess.run(
        ["gcc", "-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror", str(path), "-o", str(binary)],
        check=True,
        capture_output=True,
        timeout=30,
    )
    result = subprocess.run([str(binary)], check=True, capture_output=True, timeout=5)
    return result.stdout.decode()
