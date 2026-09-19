"""The live engine: steps SUMO through TraCI and spawns individuals as time passes (MVP-005).

The only module that talks to SUMO. *Who* spawns, *when* and *where* is decided by an
`IndividualSource` (`simulator.agents`); this module applies those decisions and observes the
result. SUMO removes individuals that reach their destination by itself — we only notice.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import traci
from traci.exceptions import FatalTraCIError, TraCIException

from simulator.agents import (
    BICYCLE_COLOR,
    BICYCLE_MAX_SPEED,
    CAR_COLOR,
    PEDESTRIAN_COLOR,
    Individual,
    IndividualSource,
    Mode,
    RandomIndividualSource,
    load_mode_edges,
)

logger = logging.getLogger(__name__)

# The simulated clock starts at 05:00 on an empty city (seconds since midnight).
START_TIME = 18000.0
# Only a real, verified fact from the MVP-004 GUI review: 200 ms per simulated second is a
# pace a human can watch. Ignored by headless `sumo`. Speed control proper is MVP-006.
DEFAULT_DELAY_MS = 200

# SUMO's own default type ids (every untyped vehicle/person uses them), plus one we create
# for bicycles by copying the car type.
CAR_TYPE_ID = "DEFAULT_VEHTYPE"
BICYCLE_TYPE_ID = "bicycle_t"
PEDESTRIAN_TYPE_ID = "DEFAULT_PEDTYPE"
VTYPE_ID: dict[Mode, str] = {
    Mode.CAR: CAR_TYPE_ID,
    Mode.BICYCLE: BICYCLE_TYPE_ID,
    Mode.PEDESTRIAN: PEDESTRIAN_TYPE_ID,
}
ID_PREFIX: dict[Mode, str] = {
    Mode.CAR: "car_",
    Mode.BICYCLE: "bike_",
    Mode.PEDESTRIAN: "ped_",
}

# Many random origin/destination pairs have no route for a mode (2 of 2 pedestrian pairs in
# the plan's spike), so a spawn retries with a fresh pair before giving up.
MAX_SPAWN_ATTEMPTS = 10
LOG_INTERVAL_SECONDS = 900  # one progress line per 15 simulated minutes


class SimulationError(RuntimeError):
    """Raised when starting the SUMO simulation fails."""


@dataclass
class EngineStats:
    """What happened during a run, per mode."""

    spawned: dict[Mode, int] = field(default_factory=lambda: dict.fromkeys(Mode, 0))
    skipped: dict[Mode, int] = field(default_factory=lambda: dict.fromkeys(Mode, 0))
    arrived: dict[Mode, int] = field(default_factory=lambda: dict.fromkeys(Mode, 0))
    active: dict[Mode, int] = field(default_factory=lambda: dict.fromkeys(Mode, 0))
    peak_active: int = 0


def format_clock(sim_time: float) -> str:
    """`HH:MM:SS` for a simulated time; wraps past 24 h since the run has no end."""
    seconds = int(sim_time) % 86400
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def _rgba(color: str) -> tuple[int, int, int, int]:
    """`"R,G,B"` (0-1 floats, SUMO config style) to the RGBA 0-255 tuple TraCI expects."""
    r, g, b = (round(float(part) * 255) for part in color.split(","))
    return (r, g, b, 255)


class LiveEngine:
    """Runs SUMO under TraCI control, spawning what `source` says is due each step."""

    def __init__(
        self,
        source: IndividualSource,
        sumo_args: list[str],
        *,
        max_sim_seconds: float | None = None,
    ) -> None:
        self._source = source
        self._sumo_args = sumo_args
        self._max_sim_seconds = max_sim_seconds
        self._counters: dict[Mode, int] = dict.fromkeys(Mode, 0)
        self._active_ids: dict[Mode, set[str]] = {mode: set() for mode in Mode}
        self._next_log = START_TIME + LOG_INTERVAL_SECONDS
        self.stats = EngineStats()

    def start(self) -> None:
        """Start SUMO and give each mode its colour (and bicycles their speed cap)."""
        try:
            traci.start(self._sumo_args)
        except (FatalTraCIError, TraCIException, OSError) as error:
            raise SimulationError(f"Could not start SUMO: {error}") from error
        self._configure_vtypes()

    def _configure_vtypes(self) -> None:
        traci.vehicletype.setColor(CAR_TYPE_ID, _rgba(CAR_COLOR))
        traci.vehicletype.setColor(PEDESTRIAN_TYPE_ID, _rgba(PEDESTRIAN_COLOR))
        traci.vehicletype.copy(CAR_TYPE_ID, BICYCLE_TYPE_ID)
        traci.vehicletype.setVehicleClass(BICYCLE_TYPE_ID, "bicycle")
        traci.vehicletype.setColor(BICYCLE_TYPE_ID, _rgba(BICYCLE_COLOR))
        traci.vehicletype.setMaxSpeed(BICYCLE_TYPE_ID, BICYCLE_MAX_SPEED)

    def _route_for(self, individual: Individual) -> list[str] | None:
        """The edges from origin to destination for the individual's mode, or None."""
        result = traci.simulation.findRoute(
            individual.origin, individual.destination, VTYPE_ID[individual.mode]
        )
        return list(result.edges) or None

    def _place(self, mode: Mode, individual_id: str, edges: list[str]) -> None:
        if mode is Mode.PEDESTRIAN:
            traci.person.add(
                individual_id, edges[0], 0, typeID=VTYPE_ID[Mode.PEDESTRIAN]
            )
            try:
                traci.person.appendWalkingStage(individual_id, edges, -1)
            except TraCIException:
                # Found by a real run: SUMO can reject a walking stage ("Invalid
                # arrivalPos") after the person was already added; without removing them
                # the person lingers, standing still, and blocks the id.
                traci.person.remove(individual_id)
                raise
            return
        # An empty route id + setRoute, not a named `route.add`: verified for real that named
        # routes are never freed (a run with no end would leak one per vehicle), while
        # these are released once the vehicle has left.
        traci.vehicle.add(individual_id, "", typeID=VTYPE_ID[mode])
        try:
            traci.vehicle.setRoute(individual_id, edges)
        except TraCIException:
            traci.vehicle.remove(individual_id)
            raise

    def spawn(self, mode: Mode) -> bool:
        """Add one individual of `mode`, retrying with a fresh pair when there is no route."""
        for _ in range(MAX_SPAWN_ATTEMPTS):
            individual = self._source.draw(mode)
            edges = self._route_for(individual)
            if edges is None:
                continue
            # Every attempt takes a fresh id, so a half-added individual from a failed
            # attempt can never collide with the next one ("person ... already exists").
            individual_id = f"{ID_PREFIX[mode]}{self._counters[mode]}"
            self._counters[mode] += 1
            try:
                self._place(mode, individual_id, edges)
            except TraCIException:
                continue
            self.stats.spawned[mode] += 1
            return True
        self.stats.skipped[mode] += 1
        return False

    def _observe(self) -> None:
        """Compare who is in the simulation now with a step ago; the difference arrived.

        Not `getArrivedNumber()`: verified for real that it does not report persons.
        """
        vehicle_ids = set(traci.vehicle.getIDList())
        person_ids = set(traci.person.getIDList())
        current = {
            Mode.CAR: {i for i in vehicle_ids if i.startswith(ID_PREFIX[Mode.CAR])},
            Mode.BICYCLE: {
                i for i in vehicle_ids if i.startswith(ID_PREFIX[Mode.BICYCLE])
            },
            Mode.PEDESTRIAN: person_ids,
        }
        for mode in Mode:
            self.stats.arrived[mode] += len(self._active_ids[mode] - current[mode])
            self._active_ids[mode] = current[mode]
            self.stats.active[mode] = len(current[mode])
        self.stats.peak_active = max(
            self.stats.peak_active, sum(self.stats.active.values())
        )

    def step(self) -> float:
        """Advance one simulated second, spawn what is due, and observe. Returns the time."""
        traci.simulationStep()
        now = traci.simulation.getTime()
        for mode in self._source.due(now):
            self.spawn(mode)
        self._observe()
        if now >= self._next_log:
            self._log_progress(now)
            self._next_log += LOG_INTERVAL_SECONDS
        return now

    def _log_progress(self, now: float) -> None:
        active = self.stats.active
        logger.info(
            "%s  active: %d cars, %d bicycles, %d pedestrians  (spawned %d, arrived %d)",
            format_clock(now),
            active[Mode.CAR],
            active[Mode.BICYCLE],
            active[Mode.PEDESTRIAN],
            sum(self.stats.spawned.values()),
            sum(self.stats.arrived.values()),
        )

    def run(self) -> EngineStats:
        """Run until the bounded time is reached, the GUI closes, or the user interrupts."""
        self.start()
        end = (
            None
            if self._max_sim_seconds is None
            else START_TIME + self._max_sim_seconds
        )
        try:
            while True:
                now = self.step()
                if end is not None and now >= end:
                    break
        except KeyboardInterrupt:
            logger.info("Interrupted — stopping")
        except FatalTraCIError:
            logger.info("SUMO closed — stopping")
        finally:
            try:
                traci.close()
            except (FatalTraCIError, TraCIException):
                pass  # connection already gone (e.g. the GUI window was closed)
        return self.stats


def _build_sumo_args(
    net_file: Path,
    *,
    headless: bool,
    gui_settings_file: Path | None,
    delay_ms: int,
) -> list[str]:
    """The `sumo`/`sumo-gui` command line: our network, empty, starting at 05:00."""
    common = [
        "-n",
        str(net_file),
        "--begin",
        str(int(START_TIME)),
        "--no-step-log",
        "true",
    ]
    if headless:
        return ["sumo", *common]
    args = ["sumo-gui", *common, "--start", "--delay", str(delay_ms)]
    if gui_settings_file is not None:
        args += ["--gui-settings-file", str(gui_settings_file)]
    return args


def run_live(
    net_file: Path,
    *,
    headless: bool,
    gui_settings_file: Path | None = None,
    seed: int | None = None,
    max_sim_seconds: float | None = None,
    delay_ms: int = DEFAULT_DELAY_MS,
) -> EngineStats:
    """Start an empty Ängelholm at 05:00 and keep spawning individuals until stopped."""
    source = RandomIndividualSource(
        load_mode_edges(net_file), start_time=START_TIME, seed=seed
    )
    sumo_args = _build_sumo_args(
        net_file,
        headless=headless,
        gui_settings_file=gui_settings_file,
        delay_ms=delay_ms,
    )
    engine = LiveEngine(source, sumo_args, max_sim_seconds=max_sim_seconds)
    return engine.run()
