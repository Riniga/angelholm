"""Smoke test: the simulator package is installed and importable."""

import simulator


def test_package_has_version():
    assert simulator.__version__ == "0.1.0"
