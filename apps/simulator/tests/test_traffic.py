"""Tests for simulator.traffic — mocked subprocess calls, no live SUMO invocation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from simulator.traffic import (
    MIN_VEHICLES,
    TrafficGenerationError,
    generate_traffic,
    write_sumocfg,
)


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="", stderr=stderr
    )


def _route_file_with_vehicles(count: int) -> str:
    vehicles = "".join(f'<vehicle id="{i}" depart="{i}.00"/>' for i in range(count))
    return f"<routes>{vehicles}</routes>"


class TestGenerateTraffic:
    def test_success_returns_route_file(self, tmp_path: Path) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "routes.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_vehicles(MIN_VEHICLES + 4))
            return _completed(0)

        with patch("simulator.traffic.subprocess.run", side_effect=fake_run):
            result = generate_traffic(net_file, route_file)

        assert result == route_file

    def test_nonzero_exit_raises_traffic_generation_error(self, tmp_path: Path) -> None:
        route_file = tmp_path / "routes.rou.xml"
        with patch(
            "simulator.traffic.subprocess.run", return_value=_completed(1, "boom")
        ):
            with pytest.raises(TrafficGenerationError, match="randomTrips.py failed"):
                generate_traffic(tmp_path / "network.net.xml", route_file)

    def test_missing_output_file_raises_traffic_generation_error(
        self, tmp_path: Path
    ) -> None:
        route_file = tmp_path / "routes.rou.xml"
        with patch("simulator.traffic.subprocess.run", return_value=_completed(0)):
            with pytest.raises(TrafficGenerationError, match="was not created"):
                generate_traffic(tmp_path / "network.net.xml", route_file)

    def test_too_few_vehicles_raises_traffic_generation_error(
        self, tmp_path: Path
    ) -> None:
        route_file = tmp_path / "routes.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_vehicles(MIN_VEHICLES - 1))
            return _completed(0)

        with patch("simulator.traffic.subprocess.run", side_effect=fake_run):
            with pytest.raises(
                TrafficGenerationError, match="Only .* vehicles generated"
            ):
                generate_traffic(tmp_path / "network.net.xml", route_file)


class TestWriteSumocfg:
    def test_writes_relative_paths_and_time_bounds(self, tmp_path: Path) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "routes.rou.xml"
        config_path = tmp_path / "sim.sumocfg"

        result = write_sumocfg(
            net_file, route_file, config_path, begin=0, end=200, delay_ms=200
        )

        assert result == config_path
        content = config_path.read_text(encoding="utf-8")
        assert 'net-file value="network.net.xml"' in content
        assert 'route-files value="routes.rou.xml"' in content
        assert 'begin value="0"' in content
        assert 'end value="200"' in content
        assert 'delay value="200"' in content

    def test_paths_relative_to_config_in_different_directory(
        self, tmp_path: Path
    ) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        net_file = data_dir / "network.net.xml"
        route_file = data_dir / "routes.rou.xml"
        config_path = tmp_path / "config" / "sim.sumocfg"

        write_sumocfg(net_file, route_file, config_path)

        content = config_path.read_text(encoding="utf-8")
        assert "../data/network.net.xml" in content.replace("\\", "/")
