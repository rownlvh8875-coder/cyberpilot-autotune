"""Exact additive CI extension recognized by the historical design audit."""


def extend(design):
    install = '      - run: python -m pip install -e ".[dev,research]"\n'
    anchor = "      - name: Prepare exact Git objects outside package source during setup\n"
    warm = (
        "          for _, revision, path, _ in design_specs():\n"
        "              if revision != design_base:\n"
        "                  git_bytes(sys.argv[1], revision, path)\n"
    )
    new_warm = (
        "          from compatibility.friction_native.bundle import "
        "reference_paths, PIN as native_pin\n"
        "          for path in reference_paths():\n"
        "              git_bytes(sys.argv[1], native_pin, path)\n"
    )
    command = (
        '          sudo unshare --net -- setpriv --reuid="$audit_uid" '
        '--regid="$audit_gid" --init-groups env PYTHONDONTWRITEBYTECODE=1 '
        'GIT_NO_LAZY_FETCH=1 "$audit_python" -m '
    )
    tail = ' --reference-checkout "$RUNNER_TEMP/knowledge-reference" --verify-history\n'
    previous = command + "tests.audit.validate_carrot_friction_patch_design" + tail
    changes = (
        (
            install + anchor,
            install + "      - run: python -m pip install pycapnp==2.1.0\n" + anchor,
        ),
        (warm, warm + new_warm),
        (previous, previous + command + "compatibility.friction_native.run" + tail),
    )
    result = design
    for old, new in changes:
        if result.count(old) != 1:
            raise ValueError("NATIVE_CI_ANCHOR_DRIFT")
        result = result.replace(old, new, 1)
    return result
