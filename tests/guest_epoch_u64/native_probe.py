"""Opt-in trusted snippet compile/run; actual kernel guards are a separate check."""

import base64
import hashlib
import json
import re
import subprocess
from pathlib import Path

INPUTS = Path(__file__).with_name("native_inputs.json")
INPUT_SHA = "73ecfc9251f2465e7dfe9421f73f5f5f0cf6ad095f1937412650551c702d4cba"
MUTATIONS = (None, "saved32", "buffer32", "signed", "format32", "mask32", "float")


def probe(owned: Path, mutation: str | None = None) -> tuple[str, ...]:
    if mutation not in MUTATIONS:
        raise ValueError("CLOSED_MUTATION_REQUIRED")
    if owned.is_symlink() or not owned.is_dir() or any(owned.iterdir()):
        raise ValueError("EMPTY_OWNED_DIRECTORY_REQUIRED")
    raw = INPUTS.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA:
        raise ValueError("NATIVE_INPUT_BYTES_DRIFT")
    data = json.loads(raw)
    parts = {
        span["claim"]: base64.b64decode(span["source_base64"]).decode("ascii")
        for row in data["files"]
        for span in row["ranges"]
    }
    if mutation == "saved32":
        parts["HELPER"] = parts["HELPER"].replace(
            "u64 cookie, scope, epoch;", "u64 cookie, scope; unsigned int epoch;"
        )
    elif mutation == "buffer32":
        parts["BUFFER"] = parts["BUFFER"].replace(
            "u64 raw_cookie, raw_scope, raw_epoch;",
            "u64 raw_cookie, raw_scope; unsigned int raw_epoch;",
        )
    elif mutation == "signed":
        parts["HELPER"] = parts["HELPER"].replace(
            "u64 cookie, scope, epoch;", "u64 cookie, scope; long long epoch;"
        )
    elif mutation == "format32":
        parts["FORMAT"] = parts["FORMAT"].replace("raw_epoch=%llu", "raw_epoch=%u")
    elif mutation == "mask32":
        parts["EMITTER"] = parts["EMITTER"].replace(
            ".raw_epoch=saved.epoch,", ".raw_epoch=(saved.epoch & 0xffffffffULL),"
        )
    elif mutation == "float":
        parts["EMITTER"] = parts["EMITTER"].replace(
            ".raw_epoch=saved.epoch,", ".raw_epoch=(u64)(double)saved.epoch,"
        )
    source = (
        r"""
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>
typedef unsigned long long u64;
typedef uint8_t u8;
#define READ_ONCE(x) (*(volatile __typeof__(x) *)&(x))
struct file {
"""
        + parts["OBJECT_FIELDS"]
        + "};\n"
        + parts["HELPER"]
        + parts["BUFFER"]
        + r"""
_Static_assert(__builtin_types_compatible_p(
  __typeof__(((struct file *)0)->cpb_epoch),u64),"object_u64");
_Static_assert(__builtin_types_compatible_p(
  __typeof__(((struct cpt_snapshot *)0)->epoch),u64),"saved_u64");
_Static_assert(__builtin_types_compatible_p(
  __typeof__(((struct cpb_record *)0)->raw_epoch),u64),"buffer_u64");
struct task_struct { int unused; };
static struct cpb_record sink;
static u64 step(struct task_struct *task, struct cpb_record payload) {
  (void)task; sink=payload; return 0;
}
"""
        + parts["EMITTER"]
        + r"""
static char output[2048];
static void seq_printf(void *m, const char *format, ...) __attribute__((format(printf,2,3)));
static void seq_printf(void *m, const char *format, ...) {
  (void)m; va_list args; va_start(args,format);
  vsnprintf(output,sizeof(output),format,args); va_end(args);
}
int main(void) {
  const u64 values[]={0ULL,1ULL,4294967295ULL,4294967296ULL,4294967297ULL,
    9007199254740991ULL,9007199254740993ULL,9223372036854775807ULL,
    9223372036854775808ULL,18446744073709551614ULL,18446744073709551615ULL};
  for (unsigned int i=0;i<sizeof(values)/sizeof(values[0]);i++) {
    struct file object={.cpl_cookie=6,.cpl_scope=0,.cpb_epoch=values[i],.cpb_origin=1};
    struct cpt_snapshot saved=cpt_take(&object);
    object=(struct file){.cpb_epoch=77};
    if (!saved.captured) return 3;
    cpt_emit_saved(NULL,5,1,saved);
    saved.epoch=99;
    if (sink.raw_epoch!=values[i]) return 4;
    void *m=NULL; struct cpb_record *e=&sink;
"""
        + parts["FORMAT"]
        + r"""
    puts(output);
  }
  struct cpt_snapshot missing={};
  if (missing.captured) return 5;
  puts("UNAVAILABLE");
  return 0;
}
"""
    )
    path, binary = owned / "epoch-probe.c", owned / "epoch-probe"
    with path.open("x") as stream:
        stream.write(source)
    subprocess.run(
        ["gcc", "-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror", str(path), "-o", str(binary)],
        check=True,
        capture_output=True,
        timeout=30,
    )
    result = subprocess.run([str(binary)], check=True, capture_output=True, timeout=5)
    lines = result.stdout.decode("ascii").splitlines()
    return tuple(
        line if line == "UNAVAILABLE" else re.findall(r" raw_epoch=([0-9]+) ", line)[0]
        for line in lines
    )
