"""Bounded trusted C snippet test: stdout is a complete, explicitly synthetic frame."""

import base64
import hashlib
import json
import subprocess
from pathlib import Path

from tests.guest_epoch_u64.native_probe import INPUT_SHA, INPUTS

MUTATIONS = (
    None,
    "saved32",
    "buffer32",
    "signed",
    "format32",
    "mask32",
    "float",
    "reread",
    "unknown_status",
    "legacy_marker",
)


def probe_frame(owned: Path, mutation: str | None = None) -> bytes:
    if type(mutation) not in (str, type(None)) or mutation not in MUTATIONS:
        raise ValueError("CLOSED_MUTATION_REQUIRED")
    if owned.is_symlink() or not owned.is_dir() or any(owned.iterdir()):
        raise ValueError("EMPTY_OWNED_DIRECTORY_REQUIRED")
    raw = INPUTS.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA:
        raise ValueError("NATIVE_INPUT_BYTES_DRIFT")
    parts = {
        span["claim"]: base64.b64decode(span["source_base64"]).decode("ascii")
        for row in json.loads(raw)["files"]
        for span in row["ranges"]
    }
    if mutation in ("saved32", "signed"):
        dtype = "unsigned int" if mutation == "saved32" else "long long"
        parts["HELPER"] = parts["HELPER"].replace(
            "u64 cookie, scope, epoch;", "u64 cookie, scope; " + dtype + " epoch;"
        )
    elif mutation == "buffer32":
        parts["BUFFER"] = parts["BUFFER"].replace(
            "u64 raw_cookie, raw_scope, raw_epoch;",
            "u64 raw_cookie, raw_scope; unsigned int raw_epoch;",
        )
    elif mutation == "format32":
        parts["FORMAT"] = parts["FORMAT"].replace("raw_epoch=%llu", "raw_epoch=%u")
    elif mutation == "mask32":
        parts["EMITTER"] = parts["EMITTER"].replace(
            ".raw_epoch=saved.epoch,", ".raw_epoch=(saved.epoch & 0xffffffffULL),"
        )
    elif mutation == "float":
        # Deliberately lossy at 2^53+1, but avoid out-of-range float→u64 UB at U64_MAX.
        parts["EMITTER"] = parts["EMITTER"].replace(
            ".raw_epoch=saved.epoch,",
            ".raw_epoch=saved.epoch <= 9007199254740993ULL ? "
            "(u64)(double)saved.epoch : saved.epoch,",
        )
    elif mutation == "unknown_status":
        parts["FORMAT"] = parts["FORMAT"].replace(
            "raw_epoch_status=OBSERVED", "raw_epoch_status=UNAVAILABLE"
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
static int output_size;
static void seq_printf(void *m, const char *format, ...) __attribute__((format(printf,2,3)));
static void seq_printf(void *m, const char *format, ...) {
  (void)m; va_list args; va_start(args,format);
  output_size=vsnprintf(output,sizeof(output),format,args); va_end(args);
}
int main(void) {
  const u64 values[]={0ULL,1ULL,4294967295ULL,4294967296ULL,4294967297ULL,
    9007199254740991ULL,9007199254740993ULL,9223372036854775807ULL,
    9223372036854775808ULL,18446744073709551614ULL,18446744073709551615ULL};
  /* Envelope/context are synthetic, not a captured kernel/guest message. */
  puts("CPR2_DRIVER ok=1");
  puts("CPR2_META version=2 profile=POST_REFERENCE_RAW_EPOCH_U64_V2 "
       "encoding=UINT64_DECIMAL_V1 case=NORMAL release=6.12.113-cptagread-u64-v2 "
       "cpus=1 capacity=512 copies=2 root=8 "
       "boot_nonce=0123456789abcdef0123456789abcdef epoch=1 seed_walk=COMPLETE");
  puts("CPR2_COUNT attempted=11 reserved=11 committed=11 failed=0 discarded=0 pending=0");
  for (unsigned int i=0;i<sizeof(values)/sizeof(values[0]);i++) {
    struct file object={.cpl_cookie=6,.cpl_scope=0,.cpb_epoch=values[i],.cpb_origin=1};
    struct cpt_snapshot saved=cpt_take(&object);
    object=(struct file){.cpb_epoch=77};
    if (!saved.captured) return 3;
    cpt_emit_saved(NULL,5,i+1,saved);
    saved.epoch=99;
    printf("CPR2_EVENT n=%u epoch=1 kind=TAG_SNAPSHOT copy=1 local=%u "
           "scope=8 actor=1 task=8 source=2 dest=9",i+1,i+1);
    void *m=NULL; struct cpb_record *e=&sink;
"""
        + parts["FORMAT"]
        + r"""
    if (output_size<0 || (unsigned int)output_size>=sizeof(output)) return 4;
    puts(output);
  }
  puts("CPR2_END");
  puts("CPR2_EXIT ok=1");
  return 0;
}
"""
    )
    if mutation == "reread":
        source = source.replace(
            "cpt_emit_saved(NULL,5,i+1,saved);", "cpt_emit_saved(NULL,5,i+1,cpt_take(&object));"
        )
    elif mutation == "legacy_marker":
        source = source.replace("CPR2_EVENT", "CPR_EVENT")
    path, binary = owned / "full-frame.c", owned / "full-frame"
    with path.open("x") as stream:
        stream.write(source)
    subprocess.run(
        ["gcc", "-std=gnu11", "-O2", "-Wall", "-Wextra", "-Werror", str(path), "-o", str(binary)],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return subprocess.run([str(binary)], check=True, capture_output=True, timeout=5).stdout
