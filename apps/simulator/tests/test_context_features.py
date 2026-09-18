"""Tests for simulator.context_features — mocked subprocess calls, no live SUMO invocation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from simulator.context_features import ContextFeatureError, build_context_features


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="", stderr=stderr
    )


class TestBuildContextFeatures:
    def test_success_returns_output_path(self, tmp_path: Path) -> None:
        osm_file = tmp_path / "extract.osm.xml"
        net_file = tmp_path / "network.net.xml"
        type_file = tmp_path / "context-features.typ.xml"
        output_path = tmp_path / "angelholm.poly.xml"

        def fake_run(*args, **kwargs):
            output_path.write_text("<additional/>")
            return _completed(0)

        with patch("simulator.context_features.subprocess.run", side_effect=fake_run):
            result = build_context_features(osm_file, net_file, output_path, type_file)

        assert result == output_path
        assert result.exists()

    def test_argv_contains_discard_and_type_file(self, tmp_path: Path) -> None:
        osm_file = tmp_path / "extract.osm.xml"
        net_file = tmp_path / "network.net.xml"
        type_file = tmp_path / "context-features.typ.xml"
        output_path = tmp_path / "angelholm.poly.xml"

        def fake_run(*args, **kwargs):
            output_path.write_text("<additional/>")
            return _completed(0)

        with patch(
            "simulator.context_features.subprocess.run", side_effect=fake_run
        ) as mock_run:
            build_context_features(osm_file, net_file, output_path, type_file)

        argv = mock_run.call_args.args[0]
        assert "polyconvert" in argv
        assert "--discard" in argv
        assert "--type-file" in argv
        type_file_index = argv.index("--type-file")
        assert argv[type_file_index + 1] == str(type_file)
        assert "--net-file" in argv
        net_file_index = argv.index("--net-file")
        assert argv[net_file_index + 1] == str(net_file)

    def test_nonzero_exit_raises_context_feature_error(self, tmp_path: Path) -> None:
        osm_file = tmp_path / "extract.osm.xml"
        net_file = tmp_path / "network.net.xml"
        type_file = tmp_path / "context-features.typ.xml"
        output_path = tmp_path / "angelholm.poly.xml"
        with patch(
            "simulator.context_features.subprocess.run",
            return_value=_completed(1, "boom"),
        ):
            with pytest.raises(ContextFeatureError, match="polyconvert failed"):
                build_context_features(osm_file, net_file, output_path, type_file)

    def test_missing_output_file_raises_context_feature_error(
        self, tmp_path: Path
    ) -> None:
        osm_file = tmp_path / "extract.osm.xml"
        net_file = tmp_path / "network.net.xml"
        type_file = tmp_path / "context-features.typ.xml"
        output_path = tmp_path / "angelholm.poly.xml"
        with patch(
            "simulator.context_features.subprocess.run", return_value=_completed(0)
        ):
            with pytest.raises(ContextFeatureError, match="was not created"):
                build_context_features(osm_file, net_file, output_path, type_file)
