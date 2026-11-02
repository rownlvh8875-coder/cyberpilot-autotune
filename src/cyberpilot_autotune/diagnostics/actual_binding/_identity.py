"""Content identities of already-provided references; never reference factories."""

from dataclasses import asdict
from hashlib import sha256

from ._codec import canonical
from .values import CaptureFreezeExpectedReference, PrelaunchExpectedReference, require


def pre_reference_identity(value: PrelaunchExpectedReference) -> str:
    require(type(value) is PrelaunchExpectedReference)
    PrelaunchExpectedReference.__post_init__(value)
    return sha256(canonical({"domain": value.contract_version, "value": asdict(value)})).hexdigest()


def post_reference_identity(value: CaptureFreezeExpectedReference) -> str:
    require(type(value) is CaptureFreezeExpectedReference)
    CaptureFreezeExpectedReference.__post_init__(value)
    return sha256(canonical({"domain": value.contract_version, "value": asdict(value)})).hexdigest()
