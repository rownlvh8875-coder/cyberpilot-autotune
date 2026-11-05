import os
import pickle
import socket

import pytest

from native_e_lab.handles import _new_directory, _new_pair


def test_pair_close_and_no_serialized_authority():
    a, b = _new_pair()
    try:
        with pytest.raises(TypeError):
            pickle.dumps(a)
        assert a.close() == "CONFIRMED"
        assert a.close() == "ALREADY_CLOSED"
    finally:
        b.close()


def test_socket_fd_reuse_does_not_close_foreign():
    a, b = _new_pair()
    raw = a._socket.fileno()
    os.close(raw)
    x, y = socket.socketpair()
    if x.fileno() != raw:
        os.dup2(x.fileno(), raw)
    try:
        assert a.close() == "LOST"
        os.fstat(raw)
    finally:
        if x.fileno() != raw:
            os.close(raw)
        x.close()
        y.close()
        b.close()


def test_directory_fd_reuse_does_not_close_foreign():
    d = _new_directory()
    raw = d._fd
    os.close(raw)
    other = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    if other != raw:
        os.dup2(other, raw)
    try:
        assert d.close() == "LOST"
        os.fstat(raw)
    finally:
        os.close(raw)
        if other != raw:
            os.close(other)
    # Lost original authority deliberately leaves only this new empty fixture residue.
    assert d.residue is not None


def test_close_uncertainty_is_not_retried(monkeypatch):
    import native_e_lab.handles as h

    a, b = _new_pair()
    calls = []
    real = h._close_socket

    def uncertain(sock):
        calls.append(1)
        real(sock)
        raise OSError("test-only unknown close")

    monkeypatch.setattr(h, "_close_socket", uncertain)
    assert a.close() == "UNKNOWN"
    assert a.close() == "UNKNOWN"
    assert len(calls) == 2
    b.close()


def test_directory_remove_failure_still_releases_original_fd(monkeypatch):
    from pathlib import Path

    d = _new_directory()
    raw = d._fd
    original = Path.rmdir

    def fail_only_ours(path):
        if path == d._path:
            raise OSError("test-only rmdir failure")
        return original(path)

    monkeypatch.setattr(Path, "rmdir", fail_only_ours)
    assert d.close() == "UNKNOWN"
    with pytest.raises(OSError):
        os.fstat(raw)
    assert d.close() == "UNKNOWN"


def test_name_replacement_does_not_remove_replacement():
    d = _new_directory()
    original = d._path.with_name(d._path.name + "-moved")
    d._path.rename(original)
    d._path.mkdir()
    marker = d._path / "external-marker"
    marker.write_bytes(b"NOT_OURS")
    assert d.close() == "NAME_REPLACED"
    assert marker.read_bytes() == b"NOT_OURS"


def test_factory_failure_closes_both_sockets_even_when_first_close_is_uncertain(monkeypatch):
    import native_e_lab.handles as h

    a, b = socket.socketpair()
    raw_a, raw_b = a.fileno(), b.fileno()
    original_close = socket.socket.close
    primary = RuntimeError("identity failure")
    monkeypatch.setattr(h.socket, "socketpair", lambda *args: (a, b))
    monkeypatch.setattr(h, "_identity", lambda fd: (_ for _ in ()).throw(primary))

    def uncertain(sock):
        original_close(sock)
        if sock is a:
            raise OSError("uncertain")

    monkeypatch.setattr(socket.socket, "close", uncertain)
    with pytest.raises(RuntimeError) as caught:
        h._new_pair()
    assert caught.value is primary
    for fd in (raw_a, raw_b):
        with pytest.raises(OSError):
            os.fstat(fd)


def test_directory_factory_metadata_failure_releases_just_acquired_fd(monkeypatch):
    import native_e_lab.handles as h

    original = h.os.open
    created = []

    def opened(*args, **kwargs):
        fd = original(*args, **kwargs)
        created.append(fd)
        return fd

    monkeypatch.setattr(h.os, "open", opened)
    monkeypatch.setattr(
        h, "_identity", lambda fd: (_ for _ in ()).throw(OSError("metadata failure"))
    )
    with pytest.raises(OSError):
        h._new_directory()
    assert len(created) == 1
    with pytest.raises(OSError):
        os.fstat(created[0])


def test_fstat_match_is_not_directory_ofd_custody(tmp_path):
    import native_e_lab.handles as h

    first = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    old_identity = h._identity(first)
    os.close(first)
    second = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert h._identity(second) == old_identity
        # No _Directory.close on a known-lost original. Identical metadata is not proof.
    finally:
        os.close(second)


def test_same_directory_reopen_cannot_be_closed_as_original(tmp_path):
    import native_e_lab.handles as h

    d = h._new_directory()
    raw = d._fd
    original_identity = h._identity(raw)
    os.close(raw)
    replacement = os.open(d._path, os.O_RDONLY | os.O_DIRECTORY)
    if replacement != raw:
        os.dup2(replacement, raw)
    try:
        assert h._identity(raw) == original_identity
        assert d.close() == "LOST"
        os.fstat(raw)
    finally:
        os.close(raw)
        if replacement != raw:
            os.close(replacement)


def test_ofd_comparison_uses_original_live_anchor(tmp_path):
    import native_e_lab.handles as h

    original = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    anchor = os.dup(original)
    other = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        assert h._identity(original) == h._identity(other)
        assert h._same_ofd(original, anchor) is True
        assert h._same_ofd(original, other) is False
    finally:
        for fd in (original, anchor, other):
            os.close(fd)


def test_ofd_comparison_unavailable_does_not_fall_back_to_fstat(monkeypatch):
    import native_e_lab.handles as h

    a, b = h._new_pair()
    monkeypatch.setattr(
        h, "_same_ofd", lambda *args: (_ for _ in ()).throw(OSError(1, "not permitted"))
    )
    raw = a._socket.fileno()
    assert a.close() == "UNKNOWN"
    assert a.close() == "UNKNOWN"
    os.fstat(raw)
    assert a._socket.fileno() == -1
    # Unknown descriptors deliberately retained until this test process exits.
    assert b.close() == "UNKNOWN"
