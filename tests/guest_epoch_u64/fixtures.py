"""Literal independently authored synthetic v2 frame; no actual v1 conversion."""

META = (
    b"CPR2_DRIVER ok=1\n"
    b"CPR2_META version=2 profile=POST_REFERENCE_RAW_EPOCH_U64_V2 encoding=UINT64_DECIMAL_V1 "
    b"case=NORMAL release=6.12.113-cptagread-u64-v2 cpus=1 capacity=512 copies=2 root=8 "
    b"boot_nonce=0123456789abcdef0123456789abcdef epoch=1 seed_walk=COMPLETE\n"
)
SNAPSHOT = (
    b"CPR2_EVENT n=1 epoch=1 kind=TAG_SNAPSHOT copy=1 local=1 scope=8 actor=1 task=8 "
    b"source=2 dest=9 fd=5 read_ordinal=1 raw_cookie=6 raw_scope=0 "
    b"raw_epoch_status=OBSERVED raw_epoch=1 raw_origin=1 "
    b"capture_stage=POST_EXISTING_REFERENCE_PRE_STORE emit_stage=SAVED_SCALARS_AFTER_STORE "
    b"generation=UNAVAILABLE lifetime=UNAVAILABLE publication=UNAVAILABLE membership=UNAVAILABLE\n"
)
FRAME = (
    META
    + b"CPR2_COUNT attempted=1 reserved=1 committed=1 failed=0 discarded=0 pending=0\n"
    + SNAPSHOT
    + b"CPR2_END\nCPR2_EXIT ok=1\n"
)
