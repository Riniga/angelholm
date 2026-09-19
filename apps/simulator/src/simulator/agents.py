"""Individuals and the source that decides who appears next, for the live engine (MVP-005).

Pure logic with no `traci` import: this module decides *who* spawns, *when* and *where*;
`simulator.engine` is the only code that talks to SUMO and applies those decisions. Later
MVPs replace `RandomIndividualSource` (statistics, zones, daily plans) without touching the
engine's stepping loop.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

import sumolib


class Mode(StrEnum):
    """How an individual travels."""

    CAR = "car"
    BICYCLE = "bicycle"
    PEDESTRIAN = "pedestrian"


# The SUMO vehicle class an edge must allow for each mode.
MODE_VCLASS: dict[Mode, str] = {
    Mode.CAR: "passenger",
    Mode.BICYCLE: "bicycle",
    Mode.PEDESTRIAN: "pedestrian",
}

# apps/simulator/src/simulator/agents.py -> apps/simulator/data
DEFAULT_ENTRY_EXIT_JSON = (
    Path(__file__).resolve().parents[2] / "data" / "entry-exit-edges.json"
)
# MVP-004 (docs/plans/004-multimodal-city.plan.md, Phase 2): weight given to a curated
# entry/exit edge relative to every other eligible edge's weight of 1. Verified for real
# against the actual network + the 8 curated edges: 200 yields ~71-74% of car trips starting
# or ending at a curated edge — comfortably above the "majority" criterion. Kept for the
# live engine, where the same bias is applied to random draws instead of randomTrips.py.
DEFAULT_ENTRY_EXIT_BOOST_WEIGHT = 200.0

# MVP-005: spawn rates (individuals per simulated second), calibrated for real against the
# live engine (docs/plans/005-live-agent-engine.plan.md Phase 5), not derived on paper.
# MVP-004's own batch rates (0.705 / 0.528 / 0.705 per second, right for a 400 s burst) are
# far too high for a run with no end: they gridlocked into ~5,000 concurrent travellers still
# growing after 2 simulated hours. Measured steady states (2 simulated hours, seed 1) scale
# roughly linearly with the rate until well past this point:
#   0.05 / 0.035 / 0.035  ->  ~110 concurrent      0.20 / 0.14 / 0.14  ->  ~430
#   0.07 / 0.05  / 0.05   ->  ~120                 0.35 / 0.25 / 0.25  ->  ~830
#   0.10 / 0.07  / 0.07   ->  ~200  (chosen)
# ~200 concurrent (about 50 cars / 45 bicycles / 105 pedestrians — pedestrians dominate the
# count because they are slow) is the project owner's own density target. Raise these to get
# a busier city; the roughly linear range ends somewhere above 0.35 cars per second.
DEFAULT_RATES: dict[Mode, float] = {
    Mode.CAR: 0.10,
    Mode.BICYCLE: 0.07,
    Mode.PEDESTRIAN: 0.07,
}

# MVP-004 Phase 5: confirmed for real that without an explicit colour, every mode falls
# back to the same SUMO default (yellow) — cars and bicycles were visually
# indistinguishable in sumo-gui. "R,G,B" (0-1 floats).
CAR_COLOR = "1,1,0"  # yellow — SUMO's own default, made explicit rather than implicit
BICYCLE_COLOR = "0,1,0"  # green
PEDESTRIAN_COLOR = "1,0,1"  # magenta — high-contrast against the map background

# MVP-004 Phase 5: SUMO's own implicit bicycle speed cap already averaged ~19 km/h vs.
# cars' ~34 km/h on this network, but the project owner watched it in sumo-gui and still
# saw bicycles as too close to car speed. An explicit, deliberately lower cap gives a
# clear, consistent gap (~14 km/h measured). In m/s, SUMO's own maxSpeed unit.
BICYCLE_MAX_SPEED = 4.17  # ~15 km/h


@dataclass(frozen=True)
class Individual:
    """One traveller: a mode and the edges they start and end on."""

    mode: Mode
    origin: str
    destination: str


@dataclass(frozen=True)
class ModeEdges:
    """The edges usable by one mode, with a relative weight for picking each."""

    edges: list[str]
    weights: list[float]


class IndividualSource(Protocol):
    """Decides who appears next. The engine asks *when*, then *who*."""

    def due(self, sim_time: float) -> list[Mode]:
        """Modes that should spawn now (one entry per individual) at `sim_time`."""
        ...

    def draw(self, mode: Mode) -> Individual:
        """A fresh origin/destination pair for `mode`."""
        ...


def load_mode_edges(
    net_file: Path,
    entry_exit_json: Path = DEFAULT_ENTRY_EXIT_JSON,
    boost_weight: float = DEFAULT_ENTRY_EXIT_BOOST_WEIGHT,
) -> dict[Mode, ModeEdges]:
    """Per mode, the network edges that allow it, with selection weights.

    Cars weight the curated entry/exit edges (`entry_exit_json`) at `boost_weight` and every
    other car edge at 1 — biasing, not restricting, as in MVP-004. Bicycles and pedestrians
    are unweighted (bias for cars only, per MVP-004's scope).
    """
    net = sumolib.net.readNet(str(net_file))
    entries = json.loads(entry_exit_json.read_text(encoding="utf-8"))["entries"]
    boosted_ids = {entry["edge_id"] for entry in entries}

    result: dict[Mode, ModeEdges] = {}
    for mode, vclass in MODE_VCLASS.items():
        edges = [edge.getID() for edge in net.getEdges() if edge.allows(vclass)]
        if mode is Mode.CAR:
            weights = [boost_weight if edge in boosted_ids else 1.0 for edge in edges]
        else:
            weights = [1.0] * len(edges)
        result[mode] = ModeEdges(edges=edges, weights=weights)
    return result


class RandomIndividualSource:
    """Seeded random source: Poisson arrivals per mode, weighted random edge pairs."""

    def __init__(
        self,
        mode_edges: dict[Mode, ModeEdges],
        rates_per_second: dict[Mode, float] | None = None,
        *,
        start_time: float,
        seed: int | None = None,
    ) -> None:
        self._mode_edges = mode_edges
        self._rates = DEFAULT_RATES if rates_per_second is None else rates_per_second
        self._rng = random.Random(seed)
        # Modes with no (or zero) rate never spawn and have no next time.
        self._next_spawn: dict[Mode, float] = {
            mode: start_time + self._rng.expovariate(rate)
            for mode, rate in self._rates.items()
            if rate > 0
        }

    def due(self, sim_time: float) -> list[Mode]:
        due_modes: list[Mode] = []
        for mode in list(self._next_spawn):
            while self._next_spawn[mode] <= sim_time:
                due_modes.append(mode)
                self._next_spawn[mode] += self._rng.expovariate(self._rates[mode])
        return due_modes

    def draw(self, mode: Mode) -> Individual:
        pool = self._mode_edges[mode]
        origin = self._rng.choices(pool.edges, weights=pool.weights)[0]
        destination = origin
        while destination == origin:
            destination = self._rng.choices(pool.edges, weights=pool.weights)[0]
        return Individual(mode=mode, origin=origin, destination=destination)
