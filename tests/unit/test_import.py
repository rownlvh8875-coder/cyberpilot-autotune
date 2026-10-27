import importlib.util


def test_package_can_be_imported_without_openpilot():
    assert importlib.util.find_spec("cyberpilot_autotune") is not None
