"""GC052–064:actual two-pass capture,explicit unavailable and no authority."""

from dataclasses import FrozenInstanceError, replace

import pytest

from tests.fixtures.audit_compatibility_capture import api, git, prepared, request


def test_stable_capture_is_not_atomic_or_admitted(tmp_path):
    root = prepared(tmp_path)
    result = api("capture").capture_checkout(request(root))
    assert result.consistency == "OBSERVED_STABLE", result
    assert result.atomicity == "NOT_ESTABLISHED" and result.integrated_admission is False
    assert result.status == "BLOCKED" and all(v is False for _, v in result.permissions)
    decision = api("capture").assess_capture(result)
    assert "SOURCE_CAPTURE_ATOMICITY" in decision.remaining_blockers
    assert "HISTORICAL_REPLAY" in decision.remaining_blockers
    assert result.partial_bundle is not None


@pytest.mark.parametrize("kind", ("file", "HEAD", "index", "ignored"))
def test_actual_mutation_between_observations_rejects(tmp_path, monkeypatch, kind):
    root = prepared(tmp_path)
    req = request(root)
    a = api("capture")
    real = a.capture_pass
    count = 0

    def changed(request, budget):
        nonlocal count
        result = real(request, budget)
        count += 1
        if count == 1:
            if kind == "file":
                (root / "a").write_bytes(b"drift\n")
            elif kind == "HEAD":
                (root / ".git/HEAD").write_bytes(b"0" * 40 + b"\n")
            elif kind == "index":
                git(root, "update-index", "--assume-unchanged", "a")
            else:
                (root / ".secret").write_bytes(b"not to be read")
        return result

    monkeypatch.setattr(a, "capture_pass", changed)
    assert a.capture_checkout(req).consistency == "REJECTED"


def test_missing_source_and_known_index_error_are_both_retained(tmp_path):
    root = prepared(tmp_path)
    req = replace(request(root), source_oids=("0" * 40,))
    git(root, "update-index", "--skip-worktree", "a")
    result = api("capture").capture_checkout(req)
    assert result.consistency == "REJECTED" and result.errors and result.unavailable


def test_fabricated_atomic_claim_not_accepted_and_empty_report_not_stable():
    c = api("contracts")
    empty = c.CaptureReport(None, None, None, (), ())
    assert empty.consistency == "UNAVAILABLE"
    with pytest.raises(TypeError):
        c.CaptureReport(None, None, None, (), (), atomicity=True)


def test_ABA_same_observed_bytes_still_does_not_prove_atomicity(tmp_path):
    root = prepared(tmp_path)
    result = api("capture").capture_checkout(request(root))
    # A change restored between all observations is not a fact any reread can prove absent.
    assert result.pass_a == result.pass_b
    assert api("capture").assess_capture(result).atomicity == "NOT_ESTABLISHED"


def test_report_nested_values_cannot_accept_mutable_foreign_data():
    c = api("contracts")
    with pytest.raises(ValueError):
        c.ObjectCapture([], (), (), (), ())
    with pytest.raises(ValueError):
        c.ControlCapture([], (), ())
    with pytest.raises(ValueError):
        c.CaptureReport(object(), None, None, (), ())


def test_report_revalidated_and_cannot_bypass_pure_core_unavailable(tmp_path):
    from tests.audit_compatibility.validation import assess_compatibility

    root = prepared(tmp_path)
    result = api("capture").capture_checkout(request(root))
    assert assess_compatibility(result.partial_bundle, None).decision == "UNAVAILABLE"
    with pytest.raises(FrozenInstanceError):
        result.pass_a.controls.identities = ()
    altered = replace(result.pass_a, index=None)
    forged = replace(result, pass_a=altered, errors=(), unavailable=())
    assert api("capture").assess_capture(forged).decision == "UNAVAILABLE"


def test_unsupported_platform_no_unsafe_open_fallback(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)
    monkeypatch.setattr(api("worktree_reader"), "capable", lambda: False)
    result = api("capture").capture_checkout(req)
    assert result.consistency == "UNAVAILABLE" and "PLATFORM_SAFE_OPEN" in result.unavailable


@pytest.mark.parametrize("raw", (None, b"\xff\n", b"ref: refs/heads/missing\n"))
def test_unreadable_or_invalid_HEAD_is_explicit(tmp_path, raw):
    root = prepared(tmp_path)
    req = request(root)
    if raw is None:
        (root / ".git/HEAD").unlink()
    else:
        (root / ".git/HEAD").write_bytes(raw)
    result = api("capture").capture_checkout(req)
    assert result.consistency != "OBSERVED_STABLE"
    assert result.errors or result.unavailable


def test_packed_HEAD_reference_uses_raw_exact_oid(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    git(root, "pack-refs", "--all", "--prune")
    assert api("capture").capture_checkout(req).consistency == "OBSERVED_STABLE"


@pytest.mark.parametrize(
    "family,mode,reason",
    (
        ("ls-files", "stagebad", "INDEX_GIT_MISMATCH"),
        ("ls-files", "othersbad", "UNTRACKED_INVENTORY_MISMATCH"),
        ("check-attr", "invalidutf", "ATTRIBUTE_FRAME"),
        ("ls-files", "raise", "TEST_GIT_UNAVAILABLE"),
        ("check-attr", "raise", "TEST_GIT_UNAVAILABLE"),
    ),
)
def test_independent_wire_contradictions_or_unavailable_are_retained(
    tmp_path, monkeypatch, family, mode, reason
):
    root = prepared(tmp_path)
    req = request(root)
    a = api("git_reader")
    original = a.GitReader.run

    def damaged(self, args, raw=b""):
        if args[0] == family:
            if mode == "raise":
                raise api("contracts").CaptureFault("TEST_GIT_UNAVAILABLE", True)
            if mode == "stagebad" and "--stage" in args:
                return b""
            if mode == "othersbad" and "--others" in args:
                return b"phantom\0"
            if mode == "invalidutf":
                return b"a\0text\0\xff\0"
        return original(self, args, raw)

    monkeypatch.setattr(a.GitReader, "run", damaged)
    r = api("capture").capture_checkout(req)
    assert reason in (*r.errors, *r.unavailable)


def test_wrong_observation_profile_never_defaults_to_C1(tmp_path):
    root = prepared(tmp_path)
    r = api("capture").capture_checkout(request(root))
    assert "WRONG_PROFILE" in api("capture").assess_capture(r, "STACK_ADOPTION_V1").errors


def test_forged_index_current_mismatch_cannot_be_hidden_by_empty_error_list(tmp_path):
    root = prepared(tmp_path)
    r = api("capture").capture_checkout(request(root))
    index = replace(r.pass_a.index, entries=())
    value = replace(r, pass_a=replace(r.pass_a, index=index), errors=(), unavailable=())
    assert "INDEX_HEAD_MISMATCH" in api("capture").assess_capture(value).errors


def test_known_wrong_attribute_vector_rejects_even_if_both_passes_claim_same(tmp_path):
    root = prepared(tmp_path)
    r = api("capture").capture_checkout(request(root))
    attrs = api("contracts").AttributeCapture((("a", (("filter", "evil"),)),))
    r = replace(
        r, pass_a=replace(r.pass_a, attributes=attrs), pass_b=replace(r.pass_b, attributes=attrs)
    )
    assert "ATTRIBUTE_POLICY" in api("capture").assess_capture(r).errors


def test_available_wrong_file_cannot_be_masked_by_other_unavailable_file(tmp_path):
    from tests.audit_compatibility.git_objects import GitImage

    root = prepared(tmp_path)
    r = api("capture").capture_checkout(request(root))
    worktree = r.pass_a.worktree
    changed = replace(worktree.files[0], image=GitImage("100644", b"known drift"))
    worktree = replace(
        worktree, files=(changed, *worktree.files[1:]), errors=(), unavailable=("OTHER_MISSING",)
    )
    r = replace(
        r,
        pass_a=replace(r.pass_a, worktree=worktree),
        pass_b=replace(r.pass_b, worktree=worktree),
        errors=(),
        unavailable=(),
    )
    assert "WORKTREE_HEAD_MISMATCH" in api("capture").assess_capture(r).errors


def test_configuration_drift_inside_a_pass_is_detected(tmp_path, monkeypatch):
    root = prepared(tmp_path)
    req = request(root)
    a = api("worktree_reader")
    real = a.read_file
    changed = False

    def read(path, *args, **kwargs):
        nonlocal changed
        result = real(path, *args, **kwargs)
        if path == str(root / ".git/config") and not changed:
            changed = True
            p = root / ".git/config"
            p.write_bytes(p.read_bytes() + b"# benign but changed\n")
        return result

    monkeypatch.setattr(a, "read_file", read)
    r = api("capture").capture_checkout(req)
    assert "CONTROL_CHANGED" in r.errors


def test_shared_source_ancestry_is_read_once_not_mistaken_for_cycle(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    initial = req.validation_head
    (root / "a").write_bytes(b"next\n")
    git(root, "commit", "--quiet", "-am", "NEXT")
    req = request(root, source_oids=(initial,))
    r = api("git_reader").read_objects(req)
    assert len(r.raw_commits) == 2 and not r.errors


def test_partial_unavailable_worktree_not_compared_to_empty_success(tmp_path):
    root = prepared(tmp_path)
    r = api("capture").capture_checkout(request(root))
    value = replace(r, pass_a=replace(r.pass_a, worktree=None), unavailable=(), errors=())
    assert api("capture").assess_capture(value).decision == "UNAVAILABLE"


def test_index_entries_are_bounded_before_full_materialization(tmp_path):
    root = prepared(tmp_path)
    req = request(root)
    req = replace(req, budget=replace(req.budget, maximum_entries=1))
    result = api("capture").capture_checkout(req)
    assert result.pass_a.index is None and "RESOURCE_LIMIT" in result.unavailable
