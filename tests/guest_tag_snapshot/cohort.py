"""Frozen prepared inputs; hashes identify bytes, not safety or authority."""

KERNEL_SHA = "7cb0f6d237aa24d3597ad687973df726601cfc388920ef5fdd0042c9d814b9df"
INIT_SHA = "095eb2f73c119465691db3c13f14260f18bacb3057f69c4fa8500c866e809442"
_PREFIX = "tests/guest_tag_snapshot/"
_OLD_PREFIX = "tests/guest_bootstrap/"
INPUTS = {
    _PREFIX + "contracts.py": "cdeb13ea4c1f6c11842be2319770a1855d6d4d72f23688ce470b272e5e8483c1",
    _PREFIX + "wire.py": "c6bdfaa7605ad708751f7fb2072dbfedaf378c52e5caded140fd7f4948dc93c1",
    _PREFIX + "model.py": "546119563dd47c49c8a31e5bd955e7a091385c6e43b1ce49c6c3f096b1f46eb0",
    _PREFIX + "image.py": "b728016ec3c2004af3ca138cfac868bcd4a4b279ba9bb1da114cf495a4b237fa",
    _PREFIX + "runner.py": "00333e46fc0c370da4651524901372c6bd789881975b1bc969ce29e5886cbd7c",
    _PREFIX + "guest/init.c": "eb588c2d7c48f2b612c7281764bb9c20e6559cbff64d7692bb3b4af5428db85d",
    _PREFIX + "kernel.patch": "78bada7bb59500a6c25d9d5e691867eccb27a3e7e5f10b9e958d8e2a308777f2",
    _PREFIX + "kernel.config": "e04f3634d01201bc809f7710a741cab337c81db40a92aa556794e7dada4f8757",
    _OLD_PREFIX
    + "kernel.patch": "3eed09131f6ce03dc4a489dfe161cd3d48576ba760abf0978d8846fd3edfc848",
}
IMAGE_SHA = {
    "NORMAL": "b65858ec570d4b03933a9adfdf498b0a6e2454b3c3662636f7df1a56885a61eb",
    "SEED_LOSS": "24293ec59a9454cd91c5f8984e28e7d82e2f29786c25bcce632fd3ba6493a668",
    "SMALL_BUFFER": "694db4fcdcd7ab524bdf4ef868887186d5d24e4b35bb7c759dc17a2bf5ee8060",
    "UNSEEDED_OFD": "6fdcee2baf09a1ae5cc068040447dd33b6c35373b0906d08ffd99594cb787d09",
    "CONSTRUCTOR_FAIL": "274fd0340ac6ab7f0282e532fa80df3a8e1e54ca4b1d8076d129f5f2556d0446",
    "SNAPSHOT_LOSS": "94d9baeed46aced031706711ad351017ece1a3adc9be6d1802742c3823f85caf",
    "POINTER_LOSS": "d23489345947b41e8df0787499404671385f88bf77c1ab14e3ec17d5ed22005b",
}
