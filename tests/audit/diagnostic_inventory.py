"""Exact added-source allowance; never suppress historical preservation checks."""

from hashlib import sha256

RUNTIME_PINS = {
    "__init__.py": "ba9d906bc6297f8bd0766ef26d514b3d6fcd1701dfa77203507266f22671cea9",
    "_codec.py": "a809c5dafb6e02b87865239cc46fbf756383e79e8f8362203849adff2f948e2c",
    "_identity.py": "d35b28e33fff05abb7a436691b64a73876cea8f04a41749e87be8bebccf935eb",
    "_linkage.py": "cd95850c53a6d16d4b51a1e524e1509c2ca2da69b95337ad96dd35ddc348c86b",
    "_schema.py": "6010f490573e8f2e7ce486c52e5d8d878158a89376ddbc76c315720708f15e5d",
    "_state.py": "a8dd4a7ec8211a56c569b1d40ae6e46b1636fd74d304e245e4d0540fa15f6636",
    "assessment.py": "1e16cfdccbe500a709c8d97a82814efa761a21bc96a603bf994503fc5bc7be36",
    "constants.py": "bec1c6f3e54359c1a1698592af7bd8f811259b4de17cbaef6c4e744b662b7e97",
    "values.py": "de98f808732c24c1ad234df64b7074c0b58e35790440acdbbef7fa013da6c3cb",
}
PINS = {"actual_binding/" + name: digest for name, digest in RUNTIME_PINS.items()}
PINS["__init__.py"] = "39e27a051483ddf86fe4452dc92ffefdd9240344c85f1406159775fad914e47d"


def verified_diagnostic_paths(root):
    prefix = "src/cyberpilot_autotune/diagnostics/"
    package = root / prefix
    actual = {
        p.relative_to(package).as_posix()
        for p in package.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    assert actual == set(PINS), "diagnostics inventory changed"
    for relative, expected in PINS.items():
        assert sha256((package / relative).read_bytes()).hexdigest() == expected, relative
    return {prefix + p for p in PINS}
