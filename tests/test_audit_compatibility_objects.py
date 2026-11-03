"""Literal Git identities and immutable supplied-object boundaries."""

import importlib
import importlib.util
import subprocess
from dataclasses import FrozenInstanceError

import pytest


def api():
    assert importlib.util.find_spec("tests.audit_compatibility") is not None, "pure core absent"
    return importlib.import_module("tests.audit_compatibility.git_objects")


def test_literal_git_blob_and_tree_identities():
    a = api()
    assert a.GitImage("100644", b"").oid == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
    assert a.GitImage("100644", b"test\n").oid == "9daeafb9864cf43055ae93beb0afd6c7d144bfa4"
    assert a.TreeSnapshot(()).oid == "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


def test_nested_tree_matches_actual_git(tmp_path):
    a = api()
    subprocess.run(["git", "init", "--bare", "--quiet", str(tmp_path)], check=True)
    image = a.GitImage("100644", b"nested\n")
    blob = (
        subprocess.check_output(
            ["git", "-C", str(tmp_path), "hash-object", "-w", "--stdin"], input=image.data
        )
        .decode()
        .strip()
    )
    subtree = (
        subprocess.check_output(
            ["git", "-C", str(tmp_path), "mktree"],
            input=f"100644 blob {blob}\tleaf.py\n".encode(),
        )
        .decode()
        .strip()
    )
    top = (
        subprocess.check_output(
            ["git", "-C", str(tmp_path), "mktree"],
            input=f"040000 tree {subtree}\tdir\n100644 blob {blob}\tdir.py\n".encode(),
        )
        .decode()
        .strip()
    )
    tree = a.TreeSnapshot((("dir/leaf.py", image), ("dir.py", image)))
    assert tree.oid == top
    assert tree == a.TreeSnapshot(tree.entries[::-1])


@pytest.mark.parametrize(
    "path",
    (
        "../a",
        "/a",
        "a//b",
        "a/./b",
        "a/../b",
        "a\\b",
        ".git/a",
        "a\0b",
        "a\nb",
        "AUX.py",
        "a.",
        "a ",
        "a:b",
        "a/*",
    ),
)
def test_unsafe_paths_are_not_normalized(path):
    a = api()
    with pytest.raises(ValueError):
        a.TreeSnapshot(((path, a.GitImage("100644", b"")),))


@pytest.mark.parametrize("paths", (("a", "a"), ("A", "a"), ("a", "a/b")))
def test_duplicate_case_and_directory_collisions_reject(paths):
    a = api()
    with pytest.raises(ValueError):
        a.TreeSnapshot(tuple((p, a.GitImage("100644", b"")) for p in paths))


@pytest.mark.parametrize(
    "mode,data",
    (("120000", b"x"), ("160000", b"x"), (True, b""), ("100644", bytearray()), ("100644", None)),
)
def test_nonregular_or_mutable_images_reject(mode, data):
    with pytest.raises(ValueError):
        api().GitImage(mode, data)


def test_values_frozen_and_commit_parent_order_retained():
    a = api()
    image = a.GitImage("100755", b"")
    with pytest.raises(FrozenInstanceError):
        image.data = b"changed"
    raw = (
        b"tree "
        + b"1" * 40
        + b"\nparent "
        + b"2" * 40
        + b"\nparent "
        + b"3" * 40
        + b"\n\nTEST_ONLY\n"
    )
    commit = a.CommitObject(raw)
    assert commit.tree == "1" * 40 and commit.parents == ("2" * 40, "3" * 40)
    assert commit.oid != a.CommitObject(raw + b"changed").oid


@pytest.mark.parametrize(
    "raw",
    (
        b"",
        b"tree x\n\n",
        b"tree " + b"A" * 40 + b"\n\n",
        b"tree " + b"1" * 40 + b"\nparent x\n\n",
        b"tree " + b"1" * 40,
    ),
)
def test_malformed_commit_objects_reject(raw):
    with pytest.raises(ValueError):
        api().CommitObject(raw)
