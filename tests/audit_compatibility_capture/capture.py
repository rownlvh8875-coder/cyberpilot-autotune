"""Explicit two-pass observations,never atomicity or historical execution proof."""

from tests.audit_compatibility.contracts import CompatibilityInputBundle

from . import worktree_reader as filesystem
from .contracts import (
    PROFILE,
    AttributeCapture,
    CaptureConsistencyDecision,
    CaptureFault,
    CapturePass,
    CaptureReport,
    CaptureRequest,
    IndexCapture,
    ReadBudget,
    WorktreeCapture,
    evaluate_report,
    need,
)
from .git_reader import GitReader, read_attributes, read_objects_with
from .worktree_reader import parse_index, preflight, read_file, read_head, read_worktree


def capture_pass(request: CaptureRequest, budget: ReadBudget) -> CapturePass:
    reader = GitReader(request, budget)
    errors, missing = set(reader.controls.errors), set(reader.controls.unavailable)
    controls = reader.controls
    if "OBJECT_FORMAT" in controls.unavailable:
        objects = read_objects_with(reader, ())
        return CapturePass(
            None, controls, objects, None, None, None, controls.errors, controls.unavailable
        )
    head = None
    index: IndexCapture | None = None
    worktree: WorktreeCapture | None = None
    attributes: AttributeCapture | None = None

    def fault(error: CaptureFault) -> None:
        (missing if error.unavailable else errors).add(error.reason)

    try:
        head, refs = read_head(request, budget)
        if head != request.validation_head:
            errors.add("HEAD_MISMATCH")
        controls = type(controls)(
            tuple(sorted((*controls.identities, *refs))), controls.errors, controls.unavailable
        )
    except CaptureFault as error:
        fault(error)
    except UnicodeError:
        errors.add("HEAD_FORMAT")
    try:
        raw, _ = read_file(request.layout.git_dir + "/index", budget)
        assert raw is not None
        index = parse_index(raw, budget)
    except CaptureFault as error:
        fault(error)
    ids = tuple(
        dict.fromkeys(
            (
                request.candidate_head,
                request.validation_head,
                *request.source_oids,
                *((request.declared_base,) if request.declared_base is not None else ()),
            )
        )
    )
    objects = read_objects_with(reader, ids)
    errors.update(objects.errors)
    missing.update(objects.unavailable)
    if index is not None and not reader.controls.errors and not reader.controls.unavailable:
        try:
            stage = reader.run(("ls-files", "--stage", "-z"))
            expected = b"".join(f"{v.mode} {v.oid} 0\t{v.path}\0".encode() for v in index.entries)
            if stage != expected:
                errors.add("INDEX_GIT_MISMATCH")
        except CaptureFault as error:
            fault(error)
    by_commit, by_tree = {v.oid: v for v in objects.raw_commits}, {v.oid: v for v in objects.trees}
    current = by_commit.get(request.validation_head)
    tree = by_tree.get(current.tree) if current is not None else None
    if tree is not None:
        worktree = read_worktree(
            request, tuple((p, image.data) for p, image in tree.entries), budget
        )
        errors.update(worktree.errors)
        missing.update(worktree.unavailable)
        if (
            not worktree.unavailable
            and not reader.controls.errors
            and not reader.controls.unavailable
        ):
            try:
                from .contracts import digest

                raw_untracked = reader.run(("ls-files", "--others", "-z"))
                observed = tuple(sorted(digest(p) for p in raw_untracked.split(b"\0")[:-1]))
                if observed != worktree.untracked_including_ignored:
                    errors.add("UNTRACKED_INVENTORY_MISMATCH")
            except CaptureFault as error:
                fault(error)
        if (
            not worktree.errors
            and not worktree.unavailable
            and not controls.errors
            and not controls.unavailable
        ):
            try:
                attributes = read_attributes(reader, tree)
            except CaptureFault as error:
                fault(error)
            except UnicodeError:
                errors.add("ATTRIBUTE_FRAME")
    after = preflight(request, budget)
    errors.update(after.errors)
    missing.update(after.unavailable)
    before_values, after_values = dict(reader.controls.identities), dict(after.identities)
    if any(before_values[p] != after_values[p] for p in before_values.keys() & after_values.keys()):
        errors.add("CONTROL_CHANGED")
    return CapturePass(
        head,
        controls,
        objects,
        index,
        worktree,
        attributes,
        tuple(sorted(errors)),
        tuple(sorted(missing)),
    )


def capture_checkout(request: CaptureRequest) -> CaptureReport:
    need(type(request) is CaptureRequest)
    CaptureRequest.__post_init__(request)
    if not filesystem.capable():
        return CaptureReport(None, None, None, (), ("PLATFORM_SAFE_OPEN",))
    budget = ReadBudget(request.budget)
    a = capture_pass(request, budget)
    b = capture_pass(request, budget)
    commits = {v.oid: v for p in (a, b) for v in p.objects.raw_commits}
    trees = {v.oid: v for p in (a, b) for v in p.objects.trees}
    bundle = CompatibilityInputBundle(
        tuple(commits.values()),
        tuple(trees.values()),
        request.candidate_head,
        request.validation_head,
        request.declared_base,
    )
    result = CaptureReport(a, b, bundle, (), ())
    evaluated = evaluate_report(result)
    return CaptureReport(a, b, bundle, evaluated.errors, evaluated.unavailable)


def assess_capture(report: CaptureReport, policy: str | None = None) -> CaptureConsistencyDecision:
    result = evaluate_report(report)
    if policy not in (None, PROFILE):
        return CaptureConsistencyDecision(
            tuple(sorted({*result.errors, "WRONG_PROFILE"})), result.unavailable
        )
    return result
