"""How much traffic the live engine spawns, and when: the demand statistics (MVP-006).

Pure logic with no `traci` import. The numbers live in a committed, human-editable JSON file
(`apps/simulator/data/demand-statistics.json`): trips per day, a 24-hour departure profile and
mode shares. This module validates that file and turns it into an arrival rate per mode for
any simulated time of day, which `simulator.agents.RandomIndividualSource` consumes through
the `Demand` protocol.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from simulator.agents import Mode

# apps/simulator/src/simulator/demand.py -> apps/simulator/data
DEFAULT_DEMAND_JSON = (
    Path(__file__).resolve().parents[2] / "data" / "demand-statistics.json"
)

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400
HOURS_PER_DAY = 24
VALID_STATUSES = ("source", "estimate")


class DemandProfileError(ValueError):
    """Raised when the demand statistics file is missing, unreadable or invalid."""


class Demand(Protocol):
    """An arrival rate per mode over the simulated day."""

    def rate(self, mode: Mode, sim_time: float) -> float:
        """Individuals of `mode` per simulated second at `sim_time`."""
        ...

    def max_rate(self, mode: Mode) -> float:
        """An upper bound of `rate(mode, t)` over all `t`."""
        ...


class ConstantDemand:
    """A fixed rate per mode, all day. Modes that are not listed never spawn."""

    def __init__(self, rates: dict[Mode, float]) -> None:
        self._rates = rates

    def rate(self, mode: Mode, sim_time: float) -> float:
        """The fixed rate for `mode`, whatever the time."""
        return self._rates.get(mode, 0.0)

    def max_rate(self, mode: Mode) -> float:
        """The same fixed rate: it never varies."""
        return self._rates.get(mode, 0.0)


@dataclass(frozen=True)
class DemandProfile:
    """Trips per day spread over the 24 hours and split between the modes.

    `hourly_weights` and `mode_shares` are normalised to sum to 1. The `*_status` fields carry
    the file's own honesty labels (`"source"` or `"estimate"`) for the log line.
    """

    total_trips_per_day: float
    hourly_weights: tuple[float, ...]
    mode_shares: dict[Mode, float]
    total_status: str = "estimate"
    hourly_status: str = "estimate"
    shares_status: str = "estimate"

    def _per_second(self, mode: Mode, weight: float) -> float:
        return (
            self.total_trips_per_day
            * weight
            * self.mode_shares.get(mode, 0.0)
            / SECONDS_PER_HOUR
        )

    def rate(self, mode: Mode, sim_time: float) -> float:
        """The clock wraps at midnight: the run has no end, so every day repeats."""
        hour = int((sim_time % SECONDS_PER_DAY) // SECONDS_PER_HOUR)
        return self._per_second(mode, self.hourly_weights[hour])

    def max_rate(self, mode: Mode) -> float:
        """The rate in the busiest hour: the ceiling used for thinning."""
        return self._per_second(mode, max(self.hourly_weights))


def _number(value: object, where: str) -> float:
    # bool is an int subclass in Python; `true` is not a number here.
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DemandProfileError(f"{where} must be a number, got {value!r}")
    return float(value)


def _block(data: dict, name: str) -> dict:
    block = data.get(name)
    if not isinstance(block, dict):
        raise DemandProfileError(f"Missing or invalid block '{name}'")
    status = block.get("status")
    if status not in VALID_STATUSES:
        raise DemandProfileError(
            f"Block '{name}' needs a 'status' of 'source' or 'estimate', got {status!r}"
        )
    return block


def _normalised(values: list[float], where: str) -> list[float]:
    if any(v < 0 for v in values):
        raise DemandProfileError(f"{where} must not contain negative values")
    total = sum(values)
    if total <= 0:
        raise DemandProfileError(f"{where} must not be all zero")
    return [v / total for v in values]


def load_demand_profile(path: Path = DEFAULT_DEMAND_JSON) -> DemandProfile:
    """Read and validate the demand statistics file.

    Raises `DemandProfileError` with a message naming the offending block for anything wrong:
    an unreadable or non-JSON file, a missing block or `status`, a non-positive total, a profile
    that does not have exactly 24 hours, negative or all-zero weights/shares.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as error:
        raise DemandProfileError(f"Cannot read {path}: {error}") from error
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise DemandProfileError(f"{path} is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise DemandProfileError(f"{path} must contain a JSON object")

    total_block = _block(data, "total_trips_per_day")
    total = _number(total_block.get("value"), "total_trips_per_day.value")
    if total <= 0:
        raise DemandProfileError("total_trips_per_day.value must be positive")

    hourly_block = _block(data, "hourly_profile")
    raw_weights = hourly_block.get("weights")
    if not isinstance(raw_weights, list) or len(raw_weights) != HOURS_PER_DAY:
        raise DemandProfileError(
            f"hourly_profile.weights must be a list of exactly {HOURS_PER_DAY} numbers "
            f"(one per hour, 00-23), got "
            f"{len(raw_weights) if isinstance(raw_weights, list) else raw_weights!r}"
        )
    weights = _normalised(
        [_number(w, "hourly_profile.weights") for w in raw_weights],
        "hourly_profile.weights",
    )

    shares_block = _block(data, "mode_shares")
    raw_shares = [
        _number(shares_block.get(mode.value), f"mode_shares.{mode.value}")
        for mode in Mode
    ]
    shares = _normalised(raw_shares, "mode_shares")

    return DemandProfile(
        total_trips_per_day=total,
        hourly_weights=tuple(weights),
        mode_shares=dict(zip(Mode, shares, strict=True)),
        total_status=total_block["status"],
        hourly_status=hourly_block["status"],
        shares_status=shares_block["status"],
    )


def describe(profile: DemandProfile) -> str:
    """One line for the log saying what the run uses and how trustworthy it is."""
    peak_hour = profile.hourly_weights.index(max(profile.hourly_weights))
    shares = " / ".join(
        f"{mode.value} {profile.mode_shares[mode] * 100:.0f} %" for mode in Mode
    )
    return (
        f"{profile.total_trips_per_day:,.0f} trips/day ({profile.total_status}); "
        f"busiest hour {peak_hour:02d}:00 with "
        f"{max(profile.hourly_weights) * 100:.1f} % of the day "
        f"({profile.hourly_status} profile); {shares} ({profile.shares_status})"
    )
