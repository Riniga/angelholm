"""Tests for simulator.traffic.

`_write_edge_weights()` is pure file I/O + sumolib parsing against a small hand-built
net.xml fixture — no mocking needed, deterministic and offline. `generate_traffic()`/
`generate_bicycle_traffic()`/`generate_pedestrian_traffic()`/`write_sumocfg()` mock
`subprocess.run` — no live SUMO invocation.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from simulator.traffic import (
    MIN_BICYCLES,
    MIN_PEDESTRIANS,
    MIN_VEHICLES,
    TrafficGenerationError,
    _write_edge_weights,
    generate_bicycle_traffic,
    generate_pedestrian_traffic,
    generate_traffic,
    write_sumocfg,
)

# A minimal net.xml with two edges: e1 allows every vclass (default lane permissions),
# e2 explicitly disallows "passenger" (still allows bicycle/pedestrian) — enough to
# exercise _write_edge_weights()'s vclass filtering without needing a full real network.
_MINIMAL_NET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<net version="1.20" junctionCornerDetail="5">
    <location netOffset="0.00,0.00" convBoundary="0.00,0.00,100.00,0.00"
        origBoundary="10.51,0.0,10.52,0.0009"
        projParameter="+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"/>
    <edge id="e1" from="n1" to="n2" priority="1">
        <lane id="e1_0" index="0" speed="13.89" length="50.00" shape="0.00,0.00 50.00,0.00"/>
    </edge>
    <edge id="e2" from="n2" to="n3" priority="1">
        <lane id="e2_0" index="0" speed="13.89" length="50.00" shape="50.00,0.00 100.00,0.00"
            disallow="passenger"/>
    </edge>
    <junction id="n1" type="priority" x="0.00" y="0.00" incLanes="" intLanes="" shape="0.00,0.00"/>
    <junction id="n2" type="priority" x="50.00" y="0.00" incLanes="e1_0" intLanes="" shape="50.00,0.00"/>
    <junction id="n3" type="priority" x="100.00" y="0.00" incLanes="e2_0" intLanes="" shape="100.00,0.00"/>
</net>
"""


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="", stderr=stderr
    )


def _route_file_with_vehicles(count: int) -> str:
    vehicles = "".join(f'<vehicle id="{i}" depart="{i}.00"/>' for i in range(count))
    return f"<routes>{vehicles}</routes>"


def _route_file_with_persons(count: int) -> str:
    persons = "".join(f'<person id="{i}" depart="{i}.00"/>' for i in range(count))
    return f"<routes>{persons}</routes>"


class TestWriteEdgeWeights:
    def test_boosts_curated_edges_and_filters_by_vclass(self, tmp_path: Path) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
        entry_exit_json = tmp_path / "entry-exit-edges.json"
        entry_exit_json.write_text(
            json.dumps({"entries": [{"edge_id": "e1", "name": "Test Street"}]}),
            encoding="utf-8",
        )
        output_prefix = tmp_path / "weights"

        src_path, dst_path = _write_edge_weights(
            net_file,
            entry_exit_json,
            output_prefix,
            vclass="passenger",
            boost_weight=50.0,
        )

        assert src_path == Path(f"{output_prefix}.src.xml")
        assert dst_path == Path(f"{output_prefix}.dst.xml")
        for path in (src_path, dst_path):
            content = path.read_text(encoding="utf-8")
            assert '<edge id="e1" value="50.0"/>' in content
            # e2 disallows "passenger" — must not appear at all for this vclass.
            assert 'id="e2"' not in content

    def test_bicycle_vclass_includes_edge_that_disallows_cars(
        self, tmp_path: Path
    ) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
        entry_exit_json = tmp_path / "entry-exit-edges.json"
        entry_exit_json.write_text(json.dumps({"entries": []}), encoding="utf-8")
        output_prefix = tmp_path / "weights"

        src_path, _ = _write_edge_weights(
            net_file,
            entry_exit_json,
            output_prefix,
            vclass="bicycle",
            boost_weight=50.0,
        )

        content = src_path.read_text(encoding="utf-8")
        assert '<edge id="e1" value="1.0"/>' in content
        assert '<edge id="e2" value="1.0"/>' in content


class TestGenerateTraffic:
    def test_success_returns_route_file(self, tmp_path: Path) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
        entry_exit_json = tmp_path / "entry-exit-edges.json"
        entry_exit_json.write_text(json.dumps({"entries": []}), encoding="utf-8")
        route_file = tmp_path / "routes.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_vehicles(MIN_VEHICLES + 4))
            return _completed(0)

        with patch("simulator.traffic.subprocess.run", side_effect=fake_run):
            result = generate_traffic(
                net_file, route_file, entry_exit_json=entry_exit_json
            )

        assert result == route_file

    def test_argv_contains_weights_prefix(self, tmp_path: Path) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
        entry_exit_json = tmp_path / "entry-exit-edges.json"
        entry_exit_json.write_text(json.dumps({"entries": []}), encoding="utf-8")
        route_file = tmp_path / "routes.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_vehicles(MIN_VEHICLES + 4))
            return _completed(0)

        with patch(
            "simulator.traffic.subprocess.run", side_effect=fake_run
        ) as mock_run:
            generate_traffic(net_file, route_file, entry_exit_json=entry_exit_json)

        argv = mock_run.call_args.args[0]
        assert "--weights-prefix" in argv
        flag_index = argv.index("--weights-prefix")
        assert argv[flag_index + 1] == str(route_file.with_name("routes.rou-weights"))

    def test_nonzero_exit_raises_traffic_generation_error(self, tmp_path: Path) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
        entry_exit_json = tmp_path / "entry-exit-edges.json"
        entry_exit_json.write_text(json.dumps({"entries": []}), encoding="utf-8")
        route_file = tmp_path / "routes.rou.xml"
        with patch(
            "simulator.traffic.subprocess.run", return_value=_completed(1, "boom")
        ):
            with pytest.raises(TrafficGenerationError, match="randomTrips.py failed"):
                generate_traffic(net_file, route_file, entry_exit_json=entry_exit_json)

    def test_missing_output_file_raises_traffic_generation_error(
        self, tmp_path: Path
    ) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
        entry_exit_json = tmp_path / "entry-exit-edges.json"
        entry_exit_json.write_text(json.dumps({"entries": []}), encoding="utf-8")
        route_file = tmp_path / "routes.rou.xml"
        with patch("simulator.traffic.subprocess.run", return_value=_completed(0)):
            with pytest.raises(TrafficGenerationError, match="was not created"):
                generate_traffic(net_file, route_file, entry_exit_json=entry_exit_json)

    def test_too_few_vehicles_raises_traffic_generation_error(
        self, tmp_path: Path
    ) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
        entry_exit_json = tmp_path / "entry-exit-edges.json"
        entry_exit_json.write_text(json.dumps({"entries": []}), encoding="utf-8")
        route_file = tmp_path / "routes.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_vehicles(MIN_VEHICLES - 1))
            return _completed(0)

        with patch("simulator.traffic.subprocess.run", side_effect=fake_run):
            with pytest.raises(
                TrafficGenerationError, match="Only .* car trips generated"
            ):
                generate_traffic(net_file, route_file, entry_exit_json=entry_exit_json)


class TestGenerateBicycleTraffic:
    def test_success_returns_route_file(self, tmp_path: Path) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "bikes.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_vehicles(MIN_BICYCLES + 4))
            return _completed(0)

        with patch("simulator.traffic.subprocess.run", side_effect=fake_run):
            result = generate_bicycle_traffic(net_file, route_file)

        assert result == route_file

    def test_argv_requests_bicycle_vehicle_class(self, tmp_path: Path) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "bikes.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_vehicles(MIN_BICYCLES + 4))
            return _completed(0)

        with patch(
            "simulator.traffic.subprocess.run", side_effect=fake_run
        ) as mock_run:
            generate_bicycle_traffic(net_file, route_file)

        argv = mock_run.call_args.args[0]
        assert "--vehicle-class" in argv
        assert argv[argv.index("--vehicle-class") + 1] == "bicycle"

    def test_too_few_bicycles_raises_traffic_generation_error(
        self, tmp_path: Path
    ) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "bikes.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_vehicles(MIN_BICYCLES - 1))
            return _completed(0)

        with patch("simulator.traffic.subprocess.run", side_effect=fake_run):
            with pytest.raises(
                TrafficGenerationError, match="Only .* bicycle trips generated"
            ):
                generate_bicycle_traffic(net_file, route_file)


class TestGeneratePedestrianTraffic:
    def test_success_returns_route_file(self, tmp_path: Path) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "peds.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_persons(MIN_PEDESTRIANS + 4))
            return _completed(0)

        with patch("simulator.traffic.subprocess.run", side_effect=fake_run):
            result = generate_pedestrian_traffic(net_file, route_file)

        assert result == route_file

    def test_argv_requests_persontrips(self, tmp_path: Path) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "peds.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_persons(MIN_PEDESTRIANS + 4))
            return _completed(0)

        with patch(
            "simulator.traffic.subprocess.run", side_effect=fake_run
        ) as mock_run:
            generate_pedestrian_traffic(net_file, route_file)

        argv = mock_run.call_args.args[0]
        assert "--persontrips" in argv

    def test_too_few_pedestrians_raises_traffic_generation_error(
        self, tmp_path: Path
    ) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "peds.rou.xml"

        def fake_run(*args, **kwargs):
            route_file.write_text(_route_file_with_persons(MIN_PEDESTRIANS - 1))
            return _completed(0)

        with patch("simulator.traffic.subprocess.run", side_effect=fake_run):
            with pytest.raises(
                TrafficGenerationError, match="Only .* pedestrian trips generated"
            ):
                generate_pedestrian_traffic(net_file, route_file)


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

    def test_no_additional_route_files_omits_them(self, tmp_path: Path) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "routes.rou.xml"
        config_path = tmp_path / "sim.sumocfg"

        write_sumocfg(net_file, route_file, config_path)

        content = config_path.read_text(encoding="utf-8")
        assert content.count("routes.rou.xml") == 1

    def test_additional_route_files_appended_comma_separated(
        self, tmp_path: Path
    ) -> None:
        net_file = tmp_path / "network.net.xml"
        route_file = tmp_path / "cars.rou.xml"
        bike_file = tmp_path / "bikes.rou.xml"
        ped_file = tmp_path / "peds.rou.xml"
        config_path = tmp_path / "sim.sumocfg"

        write_sumocfg(
            net_file,
            route_file,
            config_path,
            additional_route_files=[bike_file, ped_file],
        )

        content = config_path.read_text(encoding="utf-8")
        assert 'route-files value="cars.rou.xml,bikes.rou.xml,peds.rou.xml"' in content
