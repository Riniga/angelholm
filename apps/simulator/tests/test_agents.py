"""Tests for simulator.agents — pure logic, offline and deterministic (fixed seeds)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from simulator.agents import (
    Individual,
    Mode,
    ModeEdges,
    RandomIndividualSource,
    load_mode_edges,
)
from simulator.demand import (
    DEFAULT_DEMAND_JSON,
    ConstantDemand,
    DemandProfile,
    load_demand_profile,
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


# A steady demand for tests that do not care about time of day.
_STEADY = ConstantDemand(dict.fromkeys(Mode, 0.5))


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
            _all_modes(), ConstantDemand({Mode.CAR: 0.001}), start_time=1000.0, seed=1
        )

        assert source.due(1000.0) == []

    def test_everything_due_after_a_long_time(self) -> None:
        source = RandomIndividualSource(
            _all_modes(), ConstantDemand({Mode.CAR: 1.0}), start_time=0.0, seed=1
        )

        due = source.due(200.0)

        assert len(due) > 100
        assert set(due) == {Mode.CAR}

    def test_each_mode_spawns_when_it_has_a_rate(self) -> None:
        source = RandomIndividualSource(_all_modes(), _STEADY, start_time=0.0, seed=1)

        due = source.due(600.0)

        assert set(due) == set(Mode)

    def test_zero_rate_mode_never_spawns(self) -> None:
        source = RandomIndividualSource(
            _all_modes(),
            ConstantDemand({Mode.CAR: 1.0, Mode.BICYCLE: 0.0}),
            start_time=0.0,
            seed=1,
        )

        due = source.due(10_000.0)

        assert Mode.BICYCLE not in due
        assert Mode.PEDESTRIAN not in due  # absent from the rates dict entirely

    def test_repeated_calls_do_not_repeat_individuals(self) -> None:
        source = RandomIndividualSource(
            _all_modes(), ConstantDemand({Mode.CAR: 1.0}), start_time=0.0, seed=1
        )

        source.due(100.0)

        assert source.due(100.0) == []

    def test_rate_is_roughly_honoured_over_time(self) -> None:
        source = RandomIndividualSource(
            _all_modes(), ConstantDemand({Mode.CAR: 0.5}), start_time=0.0, seed=7
        )

        due = source.due(10_000.0)

        # Expect ~5000 arrivals; a wide tolerance keeps this robust, not flaky.
        assert 4500 < len(due) < 5500

    def test_committed_demand_can_spawn_every_mode(self) -> None:
        demand = load_demand_profile(DEFAULT_DEMAND_JSON)
        source = RandomIndividualSource(
            _all_modes(), demand, start_time=18000.0, seed=1
        )

        assert set(source.due(18000.0 + 24 * 3600)) == set(Mode)


class TestDraw:
    def test_origin_never_equals_destination(self) -> None:
        source = RandomIndividualSource(_all_modes(2), _STEADY, start_time=0.0, seed=3)

        for _ in range(200):
            individual = source.draw(Mode.CAR)
            assert individual.origin != individual.destination

    def test_returns_individual_of_the_requested_mode(self) -> None:
        source = RandomIndividualSource(_all_modes(), _STEADY, start_time=0.0, seed=3)

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
        source = RandomIndividualSource(mode_edges, _STEADY, start_time=0.0, seed=5)

        draws = [source.draw(Mode.CAR) for _ in range(2000)]
        touching = sum("curated" in (d.origin, d.destination) for d in draws)

        assert touching / len(draws) > 0.5


class TestReproducibility:
    def test_same_seed_gives_same_sequence(self) -> None:
        def sequence(seed: int) -> list:
            source = RandomIndividualSource(
                _all_modes(20), _STEADY, start_time=0.0, seed=seed
            )
            return source.due(300.0), [source.draw(Mode.CAR) for _ in range(20)]

        assert sequence(11) == sequence(11)

    def test_different_seeds_differ(self) -> None:
        def draws(seed: int) -> list[Individual]:
            source = RandomIndividualSource(
                _all_modes(50), _STEADY, start_time=0.0, seed=seed
            )
            return [source.draw(Mode.CAR) for _ in range(20)]

        assert draws(1) != draws(2)


def _busy_hour_profile(shares: dict[Mode, float] | None = None) -> DemandProfile:
    """20,000 trips/day; 08:00 is ten times as busy as every other hour."""
    weights = [1.0] * 24
    weights[8] = 10.0
    total = sum(weights)
    return DemandProfile(
        total_trips_per_day=20000,
        hourly_weights=tuple(w / total for w in weights),
        mode_shares=shares
        or {Mode.CAR: 0.6, Mode.BICYCLE: 0.15, Mode.PEDESTRIAN: 0.25},
    )


def _simulate_days(profile: DemandProfile, days: int, seed: int = 11) -> dict:
    """Drive `due()` in one-minute steps from midnight; count spawns per (day, hour, mode)."""
    source = RandomIndividualSource(_all_modes(), profile, start_time=0.0, seed=seed)
    counts: dict[tuple[int, int, Mode], int] = {}
    for minute in range(1, days * 24 * 60 + 1):
        t = minute * 60.0
        for mode in source.due(t):
            key = (int((t - 1) // 86400), int(((t - 1) % 86400) // 3600), mode)
            counts[key] = counts.get(key, 0) + 1
    return counts


@pytest.fixture(scope="module")
def counts() -> dict:
    """Four simulated days at a fixed seed, simulated once for the whole module."""
    return _simulate_days(_busy_hour_profile(), days=4)


class TestTimeVaryingArrivals:
    """Statistical checks (fixed seed, wide tolerances so they are robust, not flaky)."""

    @staticmethod
    def _hour(counts: dict, day: int, hour: int) -> int:
        return sum(counts.get((day, hour, mode), 0) for mode in Mode)

    def test_busy_hour_is_much_busier_than_quiet_hours(self, counts: dict) -> None:
        for day in range(4):
            busy = self._hour(counts, day, 8)
            quiet = sum(self._hour(counts, day, h) for h in range(24) if h != 8) / 23
            assert 8 < busy / quiet < 12  # weight ratio is 10

    def test_hourly_counts_follow_the_profile(self, counts: dict) -> None:
        # 20000 trips/day, hour 8 has 10/33 of them; quiet hours 1/33 each.
        for day in range(4):
            assert 5400 < self._hour(counts, day, 8) < 6700  # expected ~6060
            for hour in (0, 3, 12, 23):
                assert 400 < self._hour(counts, day, hour) < 820  # expected ~606

    def test_daily_total_matches_the_profile(self, counts: dict) -> None:
        for day in range(4):
            total = sum(self._hour(counts, day, h) for h in range(24))
            assert 19000 < total < 21000

    def test_mode_split_matches_the_shares(self, counts: dict) -> None:
        by_mode = {
            mode: sum(v for (_, _, m), v in counts.items() if m is mode)
            for mode in Mode
        }
        total = sum(by_mode.values())

        assert 0.58 < by_mode[Mode.CAR] / total < 0.62
        assert 0.13 < by_mode[Mode.BICYCLE] / total < 0.17
        assert 0.23 < by_mode[Mode.PEDESTRIAN] / total < 0.27
        assert by_mode[Mode.CAR] > by_mode[Mode.PEDESTRIAN] > by_mode[Mode.BICYCLE]

    def test_every_day_has_the_same_shape(self, counts: dict) -> None:
        shape = [[self._hour(counts, day, h) for h in range(24)] for day in range(4)]
        for hour in (7, 8, 9):
            values = [shape[day][hour] for day in range(4)]
            assert max(values) < 1.25 * min(values)

    def test_a_mode_with_no_share_never_spawns(self) -> None:
        profile = _busy_hour_profile({Mode.CAR: 0.7, Mode.PEDESTRIAN: 0.3})

        counts = _simulate_days(profile, days=1)

        assert not any(mode is Mode.BICYCLE for (_, _, mode) in counts)

    def test_a_single_huge_step_gives_a_full_day_of_arrivals(self) -> None:
        source = RandomIndividualSource(
            _all_modes(), _busy_hour_profile(), start_time=0.0, seed=3
        )

        due = source.due(86400.0)

        assert 19000 < len(due) < 21000

    def test_time_never_goes_backwards_into_arrivals(self) -> None:
        source = RandomIndividualSource(
            _all_modes(), _busy_hour_profile(), start_time=0.0, seed=3
        )
        first = source.due(3600.0)

        assert source.due(1800.0) == []  # an earlier time yields nothing new
        assert len(first) > 0

    def test_same_seed_gives_the_same_day(self) -> None:
        profile = _busy_hour_profile()

        assert _simulate_days(profile, days=1, seed=5) == _simulate_days(
            profile, days=1, seed=5
        )
        assert _simulate_days(profile, days=1, seed=5) != _simulate_days(
            profile, days=1, seed=6
        )
