"""Build only the checked-in fixed research supervisor in the new lab workspace."""

import hashlib
import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).parent
    for stem in ("supervisor", "domain_supervisor", "domain_worker"):
        command = [
            "cc",
            "-std=c11",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-o",
            str(root / stem),
            str(root / (stem + ".c")),
        ]
        result = subprocess.run(command, check=False)
        if result.returncode:
            return result.returncode
        (root / (stem + ".sha256")).write_text(
            hashlib.sha256((root / stem).read_bytes()).hexdigest() + "\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
