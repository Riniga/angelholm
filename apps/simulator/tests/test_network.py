"""Tests for simulator.network — mocked subprocess calls, no live network access."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from simulator.network import (
    DEFAULT_BBOX,
    NetworkBuildError,
    build_network,
    fetch_osm_extract,
)


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="", stderr=stderr
    )


class TestFetchOsmExtract:
    def test_success_returns_expected_path(self, tmp_path: Path) -> None:
        expected_file = tmp_path / "angelholm_bbox.osm.xml"

        def fake_run(*args, **kwargs):
            expected_file.write_text("<osm/>")
            return _completed(0)

        with patch("simulator.network.subprocess.run", side_effect=fake_run):
            result = fetch_osm_extract(tmp_path, bbox=DEFAULT_BBOX, prefix="angelholm")

        assert result == expected_file
        assert result.exists()

    def test_nonzero_exit_raises_network_build_error(self, tmp_path: Path) -> None:
        with patch(
            "simulator.network.subprocess.run", return_value=_completed(1, "boom")
        ):
            with pytest.raises(NetworkBuildError, match="osmGet.py failed"):
                fetch_osm_extract(tmp_path)

    def test_missing_output_file_raises_network_build_error(
        self, tmp_path: Path
    ) -> None:
        with patch("simulator.network.subprocess.run", return_value=_completed(0)):
            with pytest.raises(NetworkBuildError, match="was not created"):
                fetch_osm_extract(tmp_path)


class TestBuildNetwork:
    def test_success_returns_output_path(self, tmp_path: Path) -> None:
        osm_file = tmp_path / "extract.osm.xml"
        osm_file.write_text("<osm/>")
        output_path = tmp_path / "network.net.xml"

        def fake_run(*args, **kwargs):
            output_path.write_text("<net/>")
            return _completed(0)

        with patch("simulator.network.subprocess.run", side_effect=fake_run):
            result = build_network(osm_file, output_path)

        assert result == output_path
        assert result.exists()

    def test_nonzero_exit_raises_network_build_error(self, tmp_path: Path) -> None:
        osm_file = tmp_path / "extract.osm.xml"
        output_path = tmp_path / "network.net.xml"
        with patch(
            "simulator.network.subprocess.run", return_value=_completed(1, "bad osm")
        ):
            with pytest.raises(NetworkBuildError, match="netconvert failed"):
                build_network(osm_file, output_path)

    def test_missing_output_file_raises_network_build_error(
        self, tmp_path: Path
    ) -> None:
        osm_file = tmp_path / "extract.osm.xml"
        output_path = tmp_path / "network.net.xml"
        with patch("simulator.network.subprocess.run", return_value=_completed(0)):
            with pytest.raises(NetworkBuildError, match="was not created"):
                build_network(osm_file, output_path)
