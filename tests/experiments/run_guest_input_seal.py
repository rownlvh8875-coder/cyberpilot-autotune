"""Explicit fixed guest-only probe entrypoint; no arbitrary command interface."""

from compatibility.guest_input_seal.host_main import main

if __name__ == "__main__":
    raise SystemExit(main())
