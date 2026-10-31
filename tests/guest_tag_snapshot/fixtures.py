"""Independent literal synthetic wire, never derived from actual captures."""

META = (
    b"CPR_DRIVER ok=1\n"
    b"CPR_META version=1 profile=POST_REFERENCE_RAW_V1 case=NORMAL "
    b"release=6.12.113-cptagread-v1 cpus=1 capacity=512 copies=2 root=8 "
    b"boot_nonce=0123456789abcdef0123456789abcdef epoch=1 seed_walk=COMPLETE\n"
)
CONTEXT = "copy=1 local={local} scope=8 actor=1 task=8 source=2 dest=9"


def line(n: int, kind: str, body: str, *, local: int | None = None) -> bytes:
    return (
        f"CPR_EVENT n={n} epoch=1 kind={kind} "
        + CONTEXT.format(local=n if local is None else local)
        + " "
        + body
        + "\n"
    ).encode()


POINTER = line(1, "POINTER_READ", "fd=5 presence=PRESENT")
REFERENCE = line(2, "REFERENCE", "fd=5 read_ordinal=1")
STORE = line(3, "STORE", "fd=5 read_ordinal=1 presence=PRESENT")
SNAPSHOT = line(
    4,
    "TAG_SNAPSHOT",
    "fd=5 read_ordinal=1 raw_cookie=6 raw_scope=0 raw_epoch=1 raw_origin=1 "
    "capture_stage=POST_EXISTING_REFERENCE_PRE_STORE emit_stage=SAVED_SCALARS_AFTER_STORE "
    "generation=UNAVAILABLE lifetime=UNAVAILABLE publication=UNAVAILABLE membership=UNAVAILABLE",
)


def frame(
    rows: tuple[bytes, ...] = (POINTER, REFERENCE, STORE, SNAPSHOT),
    *,
    attempted: int = 4,
    failed: int = 0,
) -> bytes:
    return (
        META
        + f"CPR_COUNT attempted={attempted} reserved={len(rows)} committed={len(rows)} "
        f"failed={failed} discarded=0 pending=0\n".encode()
        + b"".join(rows)
        + b"CPR_END\nCPR_EXIT ok=1\n"
    )
