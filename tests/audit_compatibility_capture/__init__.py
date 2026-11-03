"""Explicit development-only read adapter. Importing this namespace performs no I/O.

C1 assumes trusted prepared roots and a trusted local Git/OS toolchain. Bounded
no-follow control scans before/after Git reads reject observed escapes;they are
not enforced confinement against adversarial concurrent swaps or unobserved ABA.
OBSERVED_STABLE means checked local observations only,never atomicity,custody,
authenticity,historical replay,ENTRY admission or application authorization.
"""
