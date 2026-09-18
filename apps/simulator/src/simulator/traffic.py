"""Generate synthetic multimodal traffic over a SUMO network and its simulation config."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import sumolib

from simulator._paths import sumo_tools_dir

logger = logging.getLogger(__name__)

MIN_VEHICLES = 10
MIN_BICYCLES = 10
MIN_PEDESTRIANS = 10
DEFAULT_BEGIN = 0
DEFAULT_END = 200
# MVP-004: bumped from MVP-002's period=5.0 (~40 cars) toward the MVP's own city-centre-
# scale floors (>=80 cars, >=60 bicycles, >=80 pedestrians) — starting points, tuned for
# real against the actual network in docs/plans/004-multimodal-city.plan.md Phase 4, not
# hard-locked here. Periods differ per mode only because each mode's target count differs
# over the same begin/end window.
DEFAULT_CAR_PERIOD = 2.5
DEFAULT_BICYCLE_PERIOD = 3.3
DEFAULT_PEDESTRIAN_PERIOD = 2.5
# sumo-gui runs a simulation step as fast as it can by default — 200 simulated seconds
# finishes in a couple of real seconds, too fast to actually watch. 200ms/step spreads
# that over ~40 real seconds instead. Ignored entirely by headless `sumo` (gui_only).
DEFAULT_DELAY_MS = 200
# Fixed, not random — matches the "Scenarios Should Be Reproducible" architectural
# principle (docs/architecture/overview.md): the same inputs must produce the same traffic.
DEFAULT_SEED = 42

# apps/simulator/src/simulator/traffic.py -> apps/simulator/data
DEFAULT_ENTRY_EXIT_JSON = (
    Path(__file__).resolve().parents[2] / "data" / "entry-exit-edges.json"
)
# MVP-004 (docs/plans/004-multimodal-city.plan.md, Phase 2): weight given to a curated
# entry/exit edge relative to every other eligible edge's weight of 1, when biasing car
# trip generation via randomTrips.py --weights-prefix. Verified for real against the
# actual network + the 8 curated edges in apps/simulator/data/entry-exit-edges.json: 200
# yields ~71% of generated car trips starting or ending at a curated edge (comfortably
# above the MVP's "majority" acceptance criterion), not just estimated from the edge
# counts.
DEFAULT_ENTRY_EXIT_BOOST_WEIGHT = 200.0


class TrafficGenerationError(RuntimeError):
    """Raised when generating traffic or writing the simulation config fails."""


def _write_edge_weights(
    net_file: Path,
    entry_exit_json: Path,
    output_prefix: Path,
    *,
    vclass: str,
    boost_weight: float,
) -> tuple[Path, Path]:
    """Write `.src.xml`/`.dst.xml` edge-weight files for `randomTrips.py --weights-prefix`.

    Every edge that allows `vclass` gets weight `1`; edges listed in `entry_exit_json`
    (by ID) get `boost_weight` instead — biasing trip generation toward them without
    restricting it exclusively. `randomTrips.py`'s own weight-file loader gives weight `0`
    to any edge *not* listed in the file at all (confirmed by reading its source,
    `LoadedProps`), so every eligible edge must be listed here for this to bias rather
    than restrict trip generation to just the curated edges.

    Returns `(src_path, dst_path)`, matching `randomTrips.py`'s own
    `<prefix>.src.xml`/`<prefix>.dst.xml` naming convention (plain string concatenation,
    not `Path`-aware suffixing).
    """
    net = sumolib.net.readNet(str(net_file))
    entries = json.loads(entry_exit_json.read_text(encoding="utf-8"))["entries"]
    boosted_ids = {entry["edge_id"] for entry in entries}

    lines = ["<edgedata>", '    <interval begin="0" end="10000">']
    for edge in net.getEdges():
        if not edge.allows(vclass):
            continue
        weight = boost_weight if edge.getID() in boosted_ids else 1.0
        lines.append(f'        <edge id="{edge.getID()}" value="{weight}"/>')
    lines.append("    </interval>")
    lines.append("</edgedata>")
    content = "\n".join(lines) + "\n"

    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    src_path = Path(f"{output_prefix}.src.xml")
    dst_path = Path(f"{output_prefix}.dst.xml")
    src_path.write_text(content, encoding="utf-8")
    dst_path.write_text(content, encoding="utf-8")
    return src_path, dst_path


def _run_random_trips(
    net_file: Path,
    route_file: Path,
    *,
    begin: int,
    end: int,
    period: float,
    seed: int,
    extra_args: list[str],
    min_count: int,
    count_tag: str,
    mode_label: str,
) -> Path:
    """Run `randomTrips.py`, shared by `generate_traffic()`/`generate_bicycle_traffic()`/
    `generate_pedestrian_traffic()`. Deterministic (fixed `seed`) for reproducibility.

    Raises `TrafficGenerationError` if fewer than `min_count` occurrences of `count_tag`
    (`"<vehicle "` or `"<person "`, depending on mode) end up in the resulting route file.
    """
    route_file.parent.mkdir(parents=True, exist_ok=True)
    random_trips_script = sumo_tools_dir() / "randomTrips.py"
    # Without an explicit -o, randomTrips.py drops its intermediate trip file as
    # trips.trips.xml in the current working directory rather than next to route_file —
    # found by actually running this, not documented behaviour. Pin it explicitly.
    trip_file = route_file.with_name(route_file.stem + ".trips.xml")

    result = subprocess.run(
        [
            sys.executable,
            str(random_trips_script),
            "-n",
            str(net_file),
            "-r",
            str(route_file),
            "-o",
            str(trip_file),
            "-b",
            str(begin),
            "-e",
            str(end),
            "-p",
            str(period),
            "--seed",
            str(seed),
            "--validate",
            *extra_args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise TrafficGenerationError(
            f"randomTrips.py failed for {mode_label} trips "
            f"(exit {result.returncode}): {result.stderr.strip()}"
        )
    if not route_file.exists():
        raise TrafficGenerationError(
            f"randomTrips.py reported success but {route_file} was not created "
            f"({mode_label})"
        )

    count = route_file.read_text(encoding="utf-8").count(count_tag)
    if count < min_count:
        raise TrafficGenerationError(
            f"Only {count} {mode_label} trips generated, need at least {min_count}"
        )
    logger.info("Generated %d %s trips over %s", count, mode_label, net_file)
    return route_file


def generate_traffic(
    net_file: Path,
    route_file: Path,
    *,
    begin: int = DEFAULT_BEGIN,
    end: int = DEFAULT_END,
    period: float = DEFAULT_CAR_PERIOD,
    seed: int = DEFAULT_SEED,
    entry_exit_json: Path = DEFAULT_ENTRY_EXIT_JSON,
    boost_weight: float = DEFAULT_ENTRY_EXIT_BOOST_WEIGHT,
) -> Path:
    """Generate random, routed car trips over `net_file`, biased toward the curated
    entry/exit edges in `entry_exit_json` via `randomTrips.py --weights-prefix` (see
    `_write_edge_weights()`)."""
    weights_prefix = route_file.with_name(route_file.stem + "-weights")
    _write_edge_weights(
        net_file,
        entry_exit_json,
        weights_prefix,
        vclass="passenger",
        boost_weight=boost_weight,
    )
    return _run_random_trips(
        net_file,
        route_file,
        begin=begin,
        end=end,
        period=period,
        seed=seed,
        extra_args=["--weights-prefix", str(weights_prefix)],
        min_count=MIN_VEHICLES,
        count_tag="<vehicle ",
        mode_label="car",
    )


def generate_bicycle_traffic(
    net_file: Path,
    route_file: Path,
    *,
    begin: int = DEFAULT_BEGIN,
    end: int = DEFAULT_END,
    period: float = DEFAULT_BICYCLE_PERIOD,
    seed: int = DEFAULT_SEED,
) -> Path:
    """Generate random bicycle trips over the parts of `net_file` that allow bicycles.

    Unlike car traffic, not biased toward the curated entry/exit edges — out of this
    MVP's scope (`docs/mvp/004-multimodal-city.md`'s Scope: entry/exit bias is required
    for car traffic only).
    """
    return _run_random_trips(
        net_file,
        route_file,
        begin=begin,
        end=end,
        period=period,
        seed=seed,
        # --prefix: cars are also <vehicle> elements with unprefixed ids ("0", "1", ...) —
        # without a distinct prefix here, loading both route files together in one
        # .sumocfg collides on id "0" and sumo refuses to start. Found by actually running
        # the combined simulation, not anticipated from either mode's docs.
        extra_args=["--vehicle-class", "bicycle", "--prefix", "bike_"],
        min_count=MIN_BICYCLES,
        count_tag="<vehicle ",
        mode_label="bicycle",
    )


def generate_pedestrian_traffic(
    net_file: Path,
    route_file: Path,
    *,
    begin: int = DEFAULT_BEGIN,
    end: int = DEFAULT_END,
    period: float = DEFAULT_PEDESTRIAN_PERIOD,
    seed: int = DEFAULT_SEED,
) -> Path:
    """Generate random pedestrian trips over the parts of `net_file` that allow
    pedestrians, via `randomTrips.py --persontrips` (person/`<walk>` trips, not vehicles).
    """
    return _run_random_trips(
        net_file,
        route_file,
        begin=begin,
        end=end,
        period=period,
        seed=seed,
        extra_args=["--persontrips", "--prefix", "ped_"],
        min_count=MIN_PEDESTRIANS,
        count_tag="<person ",
        mode_label="pedestrian",
    )


def write_sumocfg(
    net_file: Path,
    route_file: Path,
    config_path: Path,
    *,
    begin: int = DEFAULT_BEGIN,
    end: int = DEFAULT_END,
    delay_ms: int = DEFAULT_DELAY_MS,
    additional_route_files: list[Path] | None = None,
) -> Path:
    """Write a `.sumocfg` tying `net_file` and `route_file` together.

    Paths are written relative to `config_path`'s own directory, since that's how SUMO
    resolves them at run time — the files don't have to live in the same directory.
    `delay_ms` sets `sumo-gui`'s default per-step animation delay so a human can actually
    watch it run; headless `sumo` (used by `run_headless()`) ignores this `<gui_only>`
    setting entirely, so it has no effect on the automated acceptance check.
    `additional_route_files` (e.g. MVP-004's bicycle/pedestrian route files), when given,
    are appended to `route_file` as a comma-separated list — `sumo`'s own `--route-files`
    accepts multiple files this way, so cars/bicycles/pedestrians can run together without
    merging their route files into one.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    net_rel = os.path.relpath(net_file, start=config_path.parent)
    route_rels = [os.path.relpath(route_file, start=config_path.parent)]
    for extra_route_file in additional_route_files or []:
        route_rels.append(os.path.relpath(extra_route_file, start=config_path.parent))
    route_rel = ",".join(route_rels)
    config_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <input>
        <net-file value="{net_rel}"/>
        <route-files value="{route_rel}"/>
    </input>
    <time>
        <begin value="{begin}"/>
        <end value="{end}"/>
    </time>
    <gui_only>
        <delay value="{delay_ms}"/>
    </gui_only>
</configuration>
""",
        encoding="utf-8",
    )
    return config_path
