"""Tests for simulator.demand — pure logic and file I/O, offline and deterministic."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from simulator.agents import Mode
from simulator.demand import (
    DEFAULT_DEMAND_JSON,
    ConstantDemand,
    DemandProfile,
    DemandProfileError,
    describe,
    load_demand_profile,
)

_VALID = {
    "_comment": "ignored",
    "total_trips_per_day": {"value": 24000, "status": "estimate"},
    "hourly_profile": {
        "status": "estimate",
        "weights": [1.0] * 23 + [9.0],  # one very busy hour (23:00)
    },
    "mode_shares": {
        "status": "source",
        "source": "a real reference",
        "car": 6,
        "bicycle": 1.5,
        "pedestrian": 2.5,
    },
}


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "demand.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _mutated(**changes) -> dict:
    data = copy.deepcopy(_VALID)
    for dotted, value in changes.items():
        *parents, leaf = dotted.split("__")
        target = data
        for parent in parents:
            target = target[parent]
        if value is ...:
            del target[leaf]
        else:
            target[leaf] = value
    return data


class TestLoadDemandProfile:
    def test_loads_and_normalises(self, tmp_path: Path) -> None:
        profile = load_demand_profile(_write(tmp_path, _VALID))

        assert profile.total_trips_per_day == 24000
        assert len(profile.hourly_weights) == 24
        assert sum(profile.hourly_weights) == pytest.approx(1.0)
        assert profile.hourly_weights[23] == pytest.approx(9 / 32)
        assert sum(profile.mode_shares.values()) == pytest.approx(1.0)
        assert profile.mode_shares[Mode.CAR] == pytest.approx(0.6)
        assert profile.mode_shares[Mode.BICYCLE] == pytest.approx(0.15)
        assert profile.mode_shares[Mode.PEDESTRIAN] == pytest.approx(0.25)

    def test_keeps_the_status_labels(self, tmp_path: Path) -> None:
        profile = load_demand_profile(_write(tmp_path, _VALID))

        assert profile.total_status == "estimate"
        assert profile.hourly_status == "estimate"
        assert profile.shares_status == "source"

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(DemandProfileError, match="Cannot read"):
            load_demand_profile(tmp_path / "nope.json")

    def test_invalid_json(self, tmp_path: Path) -> None:
        path = tmp_path / "demand.json"
        path.write_text("{not json", encoding="utf-8")

        with pytest.raises(DemandProfileError, match="not valid JSON"):
            load_demand_profile(path)

    def test_top_level_must_be_an_object(self, tmp_path: Path) -> None:
        with pytest.raises(DemandProfileError, match="JSON object"):
            load_demand_profile(_write(tmp_path, [1, 2, 3]))

    @pytest.mark.parametrize(
        "block", ["total_trips_per_day", "hourly_profile", "mode_shares"]
    )
    def test_missing_block_is_named(self, tmp_path: Path, block: str) -> None:
        data = _mutated(**{block: ...})

        with pytest.raises(DemandProfileError, match=block):
            load_demand_profile(_write(tmp_path, data))

    @pytest.mark.parametrize("status", [None, "guess", 3])
    def test_status_must_be_source_or_estimate(
        self, tmp_path: Path, status: object
    ) -> None:
        data = _mutated(hourly_profile__status=status)

        with pytest.raises(DemandProfileError, match="hourly_profile.*status"):
            load_demand_profile(_write(tmp_path, data))

    @pytest.mark.parametrize("value", [0, -5, "many", None, True])
    def test_total_must_be_a_positive_number(
        self, tmp_path: Path, value: object
    ) -> None:
        data = _mutated(total_trips_per_day__value=value)

        with pytest.raises(DemandProfileError, match="total_trips_per_day"):
            load_demand_profile(_write(tmp_path, data))

    @pytest.mark.parametrize("count", [0, 23, 25])
    def test_profile_needs_exactly_24_hours(self, tmp_path: Path, count: int) -> None:
        data = _mutated(hourly_profile__weights=[1.0] * count)

        with pytest.raises(DemandProfileError, match="exactly 24"):
            load_demand_profile(_write(tmp_path, data))

    def test_profile_weights_must_be_a_list(self, tmp_path: Path) -> None:
        data = _mutated(hourly_profile__weights="lots")

        with pytest.raises(DemandProfileError, match="exactly 24"):
            load_demand_profile(_write(tmp_path, data))

    def test_negative_weight_is_rejected(self, tmp_path: Path) -> None:
        data = _mutated(hourly_profile__weights=[1.0] * 23 + [-1.0])

        with pytest.raises(DemandProfileError, match="negative"):
            load_demand_profile(_write(tmp_path, data))

    def test_all_zero_weights_are_rejected(self, tmp_path: Path) -> None:
        data = _mutated(hourly_profile__weights=[0] * 24)

        with pytest.raises(DemandProfileError, match="all zero"):
            load_demand_profile(_write(tmp_path, data))

    def test_non_numeric_weight_is_rejected(self, tmp_path: Path) -> None:
        data = _mutated(hourly_profile__weights=[1.0] * 23 + ["x"])

        with pytest.raises(DemandProfileError, match="hourly_profile.weights"):
            load_demand_profile(_write(tmp_path, data))

    def test_missing_mode_share_is_named(self, tmp_path: Path) -> None:
        data = _mutated(mode_shares__bicycle=...)

        with pytest.raises(DemandProfileError, match="mode_shares.bicycle"):
            load_demand_profile(_write(tmp_path, data))

    def test_negative_share_is_rejected(self, tmp_path: Path) -> None:
        data = _mutated(mode_shares__car=-1)

        with pytest.raises(DemandProfileError, match="negative"):
            load_demand_profile(_write(tmp_path, data))

    def test_all_zero_shares_are_rejected(self, tmp_path: Path) -> None:
        data = _mutated(mode_shares__car=0, mode_shares__bicycle=0)
        data["mode_shares"]["pedestrian"] = 0

        with pytest.raises(DemandProfileError, match="all zero"):
            load_demand_profile(_write(tmp_path, data))

    def test_a_zero_share_for_one_mode_is_allowed(self, tmp_path: Path) -> None:
        data = _mutated(mode_shares__bicycle=0)

        profile = load_demand_profile(_write(tmp_path, data))

        assert profile.mode_shares[Mode.BICYCLE] == 0.0


class TestDemandProfileRates:
    @pytest.fixture
    def profile(self, tmp_path: Path) -> DemandProfile:
        return load_demand_profile(_write(tmp_path, _VALID))

    def test_rate_uses_the_hour_share_and_mode_share(
        self, profile: DemandProfile
    ) -> None:
        # 23:00: 24000 trips/day * (9/32 of the day) * 0.6 cars / 3600 s
        rate = profile.rate(Mode.CAR, 23 * 3600 + 10)

        assert rate == pytest.approx(24000 * (9 / 32) * 0.6 / 3600)

    def test_rate_changes_at_the_hour_boundary(self, profile: DemandProfile) -> None:
        before = profile.rate(Mode.CAR, 23 * 3600 - 1)
        after = profile.rate(Mode.CAR, 23 * 3600)

        assert after == pytest.approx(9 * before)

    def test_rate_wraps_past_midnight(self, profile: DemandProfile) -> None:
        for hour in (0, 5, 8, 23):
            t = hour * 3600 + 100
            assert profile.rate(Mode.CAR, t + 86400) == pytest.approx(
                profile.rate(Mode.CAR, t)
            )
            assert profile.rate(Mode.CAR, t + 3 * 86400) == pytest.approx(
                profile.rate(Mode.CAR, t)
            )

    def test_max_rate_bounds_every_rate(self, profile: DemandProfile) -> None:
        for mode in Mode:
            top = profile.max_rate(mode)
            assert all(profile.rate(mode, h * 3600) <= top + 1e-12 for h in range(24))
            assert top == pytest.approx(profile.rate(mode, 23 * 3600))

    def test_a_day_of_rates_adds_up_to_the_daily_total(
        self, profile: DemandProfile
    ) -> None:
        total = sum(
            profile.rate(mode, hour * 3600) * 3600
            for mode in Mode
            for hour in range(24)
        )

        assert total == pytest.approx(profile.total_trips_per_day)

    def test_a_mode_without_share_has_rate_zero(self) -> None:
        profile = DemandProfile(
            total_trips_per_day=1000,
            hourly_weights=(1 / 24,) * 24,
            mode_shares={Mode.CAR: 1.0},
        )

        assert profile.rate(Mode.BICYCLE, 0) == 0.0
        assert profile.max_rate(Mode.BICYCLE) == 0.0


class TestConstantDemand:
    def test_rate_is_constant_all_day(self) -> None:
        demand = ConstantDemand({Mode.CAR: 0.1})

        assert demand.rate(Mode.CAR, 0) == 0.1
        assert demand.rate(Mode.CAR, 12345) == 0.1
        assert demand.max_rate(Mode.CAR) == 0.1

    def test_unlisted_mode_never_spawns(self) -> None:
        demand = ConstantDemand({Mode.CAR: 0.1})

        assert demand.rate(Mode.BICYCLE, 0) == 0.0
        assert demand.max_rate(Mode.BICYCLE) == 0.0


class TestDescribe:
    def test_says_what_is_used_and_how_trustworthy_it_is(self, tmp_path: Path) -> None:
        text = describe(load_demand_profile(_write(tmp_path, _VALID)))

        assert "24,000 trips/day (estimate)" in text
        assert "busiest hour 23:00" in text
        assert "28.1 % of the day" in text
        assert "car 60 % / bicycle 15 % / pedestrian 25 % (source)" in text


class TestCommittedFile:
    """The committed statistics must satisfy what the MVP requires of them."""

    @pytest.fixture
    def raw(self) -> dict:
        return json.loads(DEFAULT_DEMAND_JSON.read_text(encoding="utf-8"))

    @pytest.fixture
    def profile(self) -> DemandProfile:
        return load_demand_profile(DEFAULT_DEMAND_JSON)

    def test_loads(self, profile: DemandProfile) -> None:
        assert len(profile.hourly_weights) == 24

    def test_every_block_is_honestly_labelled(self, raw: dict) -> None:
        for name in ("total_trips_per_day", "hourly_profile", "mode_shares"):
            assert raw[name]["status"] in ("source", "estimate")
            assert raw[name]["source"]  # a reference, or "none" for an estimate
            if raw[name]["status"] == "source":
                assert raw[name]["source"] != "none"

    def test_the_day_has_a_rhythm(self, profile: DemandProfile) -> None:
        # quiet night, clear morning peak, clear afternoon peak
        assert max(profile.hourly_weights) >= 4 * min(profile.hourly_weights)
        night = profile.hourly_weights[3]
        assert profile.hourly_weights[7] > 5 * night
        assert profile.hourly_weights[17] > 5 * night
        assert profile.hourly_weights[5] < profile.hourly_weights[7]  # 05:00 < rush

    def test_cars_are_the_largest_group(self, profile: DemandProfile) -> None:
        car = profile.mode_shares[Mode.CAR]
        assert all(
            car > share
            for mode, share in profile.mode_shares.items()
            if mode is not Mode.CAR
        )

    def test_every_mode_can_spawn(self, profile: DemandProfile) -> None:
        assert all(profile.max_rate(mode) > 0 for mode in Mode)

    def test_the_peak_stays_under_the_measured_gridlock_ceiling(
        self, profile: DemandProfile
    ) -> None:
        # MVP-005 plan, Phase 5: traffic scaled linearly up to ~0.35 cars/s and
        # gridlocked before 0.7; keep clear headroom.
        assert profile.max_rate(Mode.CAR) < 0.30
