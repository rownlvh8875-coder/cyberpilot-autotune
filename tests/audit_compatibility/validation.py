"""Pure provided-object content assessment. Never a historical/current capture or admission."""

from typing import Any

from .contracts import (
    IO_UNAVAILABLE,
    AuditCompatibilityDecision,
    CompatibilityInputBundle,
    PinnedCompatibilityManifest,
)
from .git_objects import CommitObject, GitImage, TreeSnapshot, path_value, require
from .schema import canonical, content_rows, descriptor, validate_semantics

type Files = dict[str, GitImage]


def _ancestor(ancestor: str, tip: str, commits: dict[str, CommitObject]) -> bool | None:
    pending, seen, missing = [tip], set(), False
    while pending:
        current = pending.pop()
        if current == ancestor:
            return True
        if current in seen:
            continue
        seen.add(current)
        if current not in commits:
            missing = True
        else:
            pending.extend(commits[current].parents)
    return None if missing else False


def _delta(before: Files, after: Files) -> set[str]:
    return {p for p in before.keys() | after.keys() if before.get(p) != after.get(p)}


def _postimages(
    rows: list[dict[str, Any]],
    pin: PinnedCompatibilityManifest,
    sources: dict[str, Files | None],
    q: Files,
) -> tuple[Files, set[str], set[str]]:
    posts: Files = {}
    deleted, inert = set(), set()
    for row in rows:
        path = row["path"]
        pre = row["source_preimages"]
        require(type(pre) is dict and set(pre) == set(sources))
        for name, files in sources.items():
            if files is not None:
                require(canonical(pre[name]) == canonical(descriptor(files.get(path))))
        spec, frozen = row["postimage"], row["inert_postimage_path"]
        if spec is None:
            require(frozen is None and row["operation"] == "DELETE")
            require(any(files is None or path in files for files in sources.values()))
            deleted.add(path)
        else:
            require(type(spec) is dict and path_value(frozen))
            image = q.get(frozen)
            require(image is not None and image.mode == "100644")
            assert image is not None
            require(canonical(spec) == canonical(descriptor(image)))
            require(frozen == pin.inert_root + "/" + image.sha256 + ".blob")
            require(row["operation"] in ("MODIFY", "ADD"))
            if all(files is not None for files in sources.values()):
                operation = (
                    "MODIFY"
                    if any(files is not None and path in files for files in sources.values())
                    else "ADD"
                )
                require(row["operation"] == operation)
            posts[path] = image
            inert.add(frozen)
    return posts, deleted, inert


def _expected(m: Files, q: Files, o: Files, posts: Files, deleted: set[str]) -> Files:
    expected: Files = {}
    for path in m.keys() | q.keys() | o.keys():
        base, left, right = m.get(path), q.get(path), o.get(path)
        if left == right or right == base:
            chosen = left
        elif left == base:
            chosen = right
        else:
            require(path in posts or path in deleted)
            chosen = None
        if chosen is not None:
            expected[path] = chosen
    expected.update(posts)
    for path in deleted:
        expected.pop(path, None)
    # Also reject cross-side directory/case collisions before comparing the whole supplied tree.
    TreeSnapshot(tuple(expected.items()))
    return expected


def assess_compatibility(
    bundle: CompatibilityInputBundle, manifest: PinnedCompatibilityManifest | None
) -> AuditCompatibilityDecision:
    require(type(bundle) is CompatibilityInputBundle)
    CompatibilityInputBundle.__post_init__(bundle)
    errors: set[str] = set()
    missing = set(IO_UNAVAILABLE)
    if manifest is None:
        missing.add("PINNED_MANIFEST")
        return AuditCompatibilityDecision((), tuple(sorted(missing)))
    require(type(manifest) is PinnedCompatibilityManifest)
    PinnedCompatibilityManifest.__post_init__(manifest)
    commits = {c.oid: c for c in bundle.commits}
    trees = {t.oid: dict(t.entries) for t in bundle.trees}

    def get_commit(identity: str | None, role: str) -> CommitObject | None:
        result = commits.get(identity) if identity is not None else None
        if result is None:
            missing.add("COMMIT_" + role)
        return result

    def get_files(commit: CommitObject | None, role: str) -> Files | None:
        if commit is None:
            return None
        result = trees.get(commit.tree)
        if result is None:
            missing.add("TREE_" + role)
        return result

    def check(condition: bool, reason: str) -> None:
        if not condition:
            errors.add(reason)

    m, d, o, r = (
        get_commit(identity, role)
        for role, identity in (
            ("M", manifest.m),
            ("D", manifest.d),
            ("O", manifest.o),
            ("R", manifest.r),
        )
    )
    candidate = get_commit(bundle.candidate_head, "CANDIDATE")
    validation = get_commit(bundle.validation_head, "VALIDATION")
    q = None
    if candidate is not None:
        check(len(candidate.parents) == 2 and candidate.parents[1] == manifest.o, "I_PARENT_ORDER")
        if candidate.parents:
            q = get_commit(candidate.parents[0], "Q")
    if r is not None:
        check(r.parents == (manifest.d,), "R_PARENT")
    if q is not None:
        check(q.parents == (manifest.r,), "Q_PARENT")
    for role, tip in (("D", manifest.d), ("O", manifest.o)):
        ancestry = _ancestor(manifest.m, tip, commits)
        if ancestry is None:
            missing.add("ANCESTRY_" + role)
        else:
            check(ancestry, "SOURCE_ANCESTRY_" + role)
    if validation is not None and validation.oid != bundle.candidate_head:
        check(len(validation.parents) == 2, "VIRTUAL_PARENT_COUNT")
        if len(validation.parents) == 2:
            check(validation.parents[1] == bundle.candidate_head, "VIRTUAL_CANDIDATE_PARENT")
            if bundle.declared_base is None:
                missing.add("DECLARED_BASE")
            else:
                check(validation.parents[0] == bundle.declared_base, "VIRTUAL_BASE_PARENT")
                get_commit(bundle.declared_base, "DECLARED_BASE")

    mf, df, of, rf, qf, cf, vf = (
        get_files(commit, role)
        for role, commit in (
            ("M", m),
            ("D", d),
            ("O", o),
            ("R", r),
            ("Q", q),
            ("CANDIDATE", candidate),
            ("VALIDATION", validation),
        )
    )
    if rf is not None:
        try:
            image = rf.get(manifest.semantic_path)
            require(image is not None and image.mode == "100644")
            assert image is not None
            validate_semantics(image.data, manifest)
        except ValueError:
            errors.add("R_SEMANTICS")
    if rf is not None and df is not None:
        check(_delta(df, rf) == set(manifest.semantic_paths), "R_DELTA")
        check(
            all(
                p not in df and p in rf and rf[p].mode == "100644" for p in manifest.semantic_paths
            ),
            "R_METADATA_ONLY_ADDITIONS",
        )
    rows = None
    if qf is not None:
        try:
            image = qf.get(manifest.manifest_path)
            require(image is not None and image.mode == "100644")
            assert image is not None
            rows = content_rows(image.data, manifest)
        except ValueError:
            errors.add("Q_SCHEMA")
    if rows is not None and qf is not None:
        try:
            posts, deleted, inert = _postimages(rows, manifest, {"M": mf, "D": df, "O": of}, qf)
        except ValueError:
            errors.add("Q_TRANSITIONS")
        else:
            if rf is not None:
                additions = inert | {manifest.manifest_path}
                check(_delta(rf, qf) == additions and not additions & rf.keys(), "Q_DELTA")
            if mf is not None and of is not None:
                try:
                    expected = _expected(mf, qf, of, posts, deleted)
                except ValueError:
                    errors.add("THREE_WAY_CONFLICT")
                else:
                    if cf is not None:
                        check(cf == expected, "CURRENT_TREE")
                    if vf is not None:
                        check(vf == expected, "VALIDATION_TREE")
    return AuditCompatibilityDecision(tuple(sorted(errors)), tuple(sorted(missing)))
