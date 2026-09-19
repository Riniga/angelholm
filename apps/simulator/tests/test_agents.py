"""Tests for simulator.agents — pure logic, offline and deterministic (fixed seeds)."""

from __future__ import annotations

import json
from pathlib import Path

from simulator.agents import (
    DEFAULT_RATES,
    Individual,
    Mode,
    ModeEdges,
    RandomIndividualSource,
    load_mode_edges,
)

# e1 allows every vclass, e2 disallows "passenger" (bicycle/pedestrian still allowed).
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


def _write_inputs(tmp_path: Path, curated: list[str]) -> tuple[Path, Path]:
    net_file = tmp_path / "test.net.xml"
    net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
    entry_exit_json = tmp_path / "entry-exit-edges.json"
    entry_exit_json.write_text(
        json.dumps({"entries": [{"edge_id": e, "name": "x"} for e in curated]}),
        encoding="utf-8",
    )
    return net_file, entry_exit_json


def _pool(count: int, *, weights: list[float] | None = None) -> ModeEdges:
    edges = [f"edge{i}" for i in range(count)]
    return ModeEdges(edges=edges, weights=weights or [1.0] * count)


def _all_modes(count: int = 5) -> dict[Mode, ModeEdges]:
    return {mode: _pool(count) for mode in Mode}


class TestLoadModeEdges:
    def test_filters_edges_by_mode(self, tmp_path: Path) -> None:
        net_file, entry_exit_json = _write_inputs(tmp_path, curated=[])

        result = load_mode_edges(net_file, entry_exit_json, boost_weight=50.0)

        assert result[Mode.CAR].edges == ["e1"]  # e2 disallows passenger
        assert sorted(result[Mode.BICYCLE].edges) == ["e1", "e2"]
        assert sorted(result[Mode.PEDESTRIAN].edges) == ["e1", "e2"]

    def test_boosts_curated_edges_for_cars_only(self, tmp_path: Path) -> None:
        net_file, entry_exit_json = _write_inputs(tmp_path, curated=["e1"])

        result = load_mode_edges(net_file, entry_exit_json, boost_weight=50.0)

        assert result[Mode.CAR].weights == [50.0]
        assert result[Mode.BICYCLE].weights == [1.0, 1.0]
        assert result[Mode.PEDESTRIAN].weights == [1.0, 1.0]

    def test_non_curated_car_edge_gets_weight_one(self, tmp_path: Path) -> None:
        net_file, entry_exit_json = _write_inputs(tmp_path, curated=["e2"])

        result = load_mode_edges(net_file, entry_exit_json, boost_weight=50.0)

        # e2 is curated but not car-capable: it must not appear for cars at all.
        assert result[Mode.CAR].edges == ["e1"]
        assert result[Mode.CAR].weights == [1.0]

    def test_defaults_point_at_the_committed_entry_exit_file(self) -> None:
        from simulator.agents import DEFAULT_ENTRY_EXIT_JSON

        entries = json.loads(DEFAULT_ENTRY_EXIT_JSON.read_text(encoding="utf-8"))
        assert len(entries["entries"]) == 8


class TestDue:
    def test_nothing_due_before_the_first_spawn_time(self) -> None:
        source = RandomIndividualSource(
            _all_modes(), {Mode.CAR: 0.001}, start_time=1000.0, seed=1
        )

        assert source.due(1000.0) == []

    def test_everything_due_after_a_long_time(self) -> None:
        source = RandomIndividualSource(
            _all_modes(), {Mode.CAR: 1.0}, start_time=0.0, seed=1
        )

        due = source.due(200.0)

        assert len(due) > 100
        assert set(due) == {Mode.CAR}

    def test_each_mode_spawns_when_it_has_a_rate(self) -> None:
        source = RandomIndividualSource(_all_modes(), start_time=0.0, seed=1)

        due = source.due(600.0)

        assert set(due) == set(Mode)

    def test_zero_rate_mode_never_spawns(self) -> None:
        source = RandomIndividualSource(
            _all_modes(),
            {Mode.CAR: 1.0, Mode.BICYCLE: 0.0},
            start_time=0.0,
            seed=1,
        )

        due = source.due(10_000.0)

        assert Mode.BICYCLE not in due
        assert Mode.PEDESTRIAN not in due  # absent from the rates dict entirely

    def test_repeated_calls_do_not_repeat_individuals(self) -> None:
        source = RandomIndividualSource(
            _all_modes(), {Mode.CAR: 1.0}, start_time=0.0, seed=1
        )

        source.due(100.0)

        assert source.due(100.0) == []

    def test_rate_is_roughly_honoured_over_time(self) -> None:
        source = RandomIndividualSource(
            _all_modes(), {Mode.CAR: 0.5}, start_time=0.0, seed=7
        )

        due = source.due(10_000.0)

        # Expect ~5000 arrivals; a wide tolerance keeps this robust, not flaky.
        assert 4500 < len(due) < 5500

    def test_default_rates_cover_every_mode(self) -> None:
        assert set(DEFAULT_RATES) == set(Mode)
        assert all(rate > 0 for rate in DEFAULT_RATES.values())


class TestDraw:
    def test_origin_never_equals_destination(self) -> None:
        source = RandomIndividualSource(_all_modes(2), start_time=0.0, seed=3)

        for _ in range(200):
            individual = source.draw(Mode.CAR)
            assert individual.origin != individual.destination

    def test_returns_individual_of_the_requested_mode(self) -> None:
        source = RandomIndividualSource(_all_modes(), start_time=0.0, seed=3)

        individual = source.draw(Mode.BICYCLE)

        assert isinstance(individual, Individual)
        assert individual.mode is Mode.BICYCLE

    def test_curated_edges_are_favoured(self) -> None:
        # 1 curated edge (weight 200) among 100 others (weight 1): P(either endpoint is
        # curated) is high; well above the "majority" criterion.
        edges = ["curated"] + [f"e{i}" for i in range(100)]
        weights = [200.0] + [1.0] * 100
        mode_edges = _all_modes()
        mode_edges[Mode.CAR] = ModeEdges(edges=edges, weights=weights)
        source = RandomIndividualSource(mode_edges, start_time=0.0, seed=5)

        draws = [source.draw(Mode.CAR) for _ in range(2000)]
        touching = sum("curated" in (d.origin, d.destination) for d in draws)

        assert touching / len(draws) > 0.5


class TestReproducibility:
    def test_same_seed_gives_same_sequence(self) -> None:
        def sequence(seed: int) -> list:
            source = RandomIndividualSource(_all_modes(20), start_time=0.0, seed=seed)
            return source.due(300.0), [source.draw(Mode.CAR) for _ in range(20)]

        assert sequence(11) == sequence(11)

    def test_different_seeds_differ(self) -> None:
        def draws(seed: int) -> list[Individual]:
            source = RandomIndividualSource(_all_modes(50), start_time=0.0, seed=seed)
            return [source.draw(Mode.CAR) for _ in range(20)]

        assert draws(1) != draws(2)
