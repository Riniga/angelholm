"""Generate synthetic multimodal traffic over a SUMO network and its simulation config."""

from __future__ import annotations

import json
import logging
import os
import re
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
# MVP-004 Phase 5: bumped from MVP-002's 200 — the project owner asked for more time to
# watch the simulation run. Periods below are recomputed for this longer window to hold
# the same target counts (~280 cars / ~210 bicycles / ~280 pedestrians) steady rather than
# also doubling the traffic volume, which wasn't asked for.
DEFAULT_END = 400
# MVP-004: bumped from MVP-002's period=5.0 (~40 cars) toward the MVP's own city-centre-
# scale floors (>=80 cars, >=60 bicycles, >=80 pedestrians) — starting points, tuned for
# real against the actual network in docs/plans/004-multimodal-city.plan.md Phase 4, not
# hard-locked here. Periods differ per mode only because each mode's target count differs
# over the same begin/end window. Bumped again, Phase 5: the project owner reviewed the
# first (80/61/80) pass live in sumo-gui and asked for ~3-4x more — periods below target
# ~280 cars / ~210 bicycles / ~280 pedestrians, confirmed against real generated counts,
# not just this division; then re-derived again for DEFAULT_END's 200 -> 400 bump above,
# to keep those same target counts rather than doubling them.
DEFAULT_CAR_PERIOD = 1.42
DEFAULT_BICYCLE_PERIOD = 1.9
DEFAULT_PEDESTRIAN_PERIOD = 1.42
# sumo-gui runs a simulation step as fast as it can by default — hundreds of simulated
# seconds finish in a couple of real seconds, too fast to actually watch. 200ms/step
# spreads DEFAULT_END's 400 simulated seconds over ~80 real seconds instead. Ignored
# entirely by headless `sumo` (gui_only).
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
# yields ~71-74% of generated car trips (measured at both 80 and 282 trips) starting or
# ending at a curated edge — comfortably above the MVP's "majority" acceptance
# criterion, not just estimated from the edge counts.
DEFAULT_ENTRY_EXIT_BOOST_WEIGHT = 200.0

# MVP-004 Phase 5: confirmed for real that without an explicit colour, every mode falls
# back to the same SUMO default (yellow) — cars and bicycles were visually
# indistinguishable in sumo-gui. "R,G,B" (0-1 floats), the format SUMO's <vType color=...>
# expects.
CAR_COLOR = "1,1,0"  # yellow — SUMO's own default, made explicit rather than implicit
BICYCLE_COLOR = "0,1,0"  # green
PEDESTRIAN_COLOR = "1,0,1"  # magenta — high-contrast against the map background

# MVP-004 Phase 5: SUMO's own implicit bicycle speed cap already averaged ~19 km/h vs.
# cars' ~34 km/h on this network (confirmed via sumo --tripinfo-output), but the project
# owner watched it in sumo-gui and still saw bicycles as too close to car speed. An
# explicit, deliberately lower cap gives a clear, consistent gap (~14 km/h measured after
# this was applied). In m/s, SUMO's own <vType maxSpeed=...> unit.
BICYCLE_MAX_SPEED = 4.17  # ~15 km/h


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


def _customize_vtype(
    route_file: Path,
    color: str,
    default_type_id: str,
    default_vclass: str,
    *,
    max_speed: float | None = None,
) -> None:
    """Give `route_file`'s vehicles/persons an explicit `color` (and, optionally,
    `max_speed` in m/s), so different modes render distinguishably — and move
    realistically relative to each other — in `sumo-gui`. Confirmed for real that with no
    explicit colour anywhere, every mode falls back to the same default and is visually
    indistinguishable (see `BICYCLE_MAX_SPEED` for why speed is set explicitly too).

    Plain text substitution/insertion, not full XML parsing: the file's shape is fully
    known (our own `randomTrips.py` output), and this avoids importing the stdlib
    `xml.etree.ElementTree` for element construction, which would re-trigger the same
    `python.lang.security.use-defused-xml` SAST finding `defusedxml` was already adopted
    for elsewhere in this codebase (`simulator.context_features`).

    If `randomTrips.py` already generated a `<vType>` (e.g. bicycles, via
    `--vehicle-class`), customises it in place. Otherwise (e.g. cars, pedestrians — left
    fully implicit by `randomTrips.py`) inserts one using SUMO's own internal default
    type id (`default_type_id`, e.g. `"DEFAULT_VEHTYPE"`/`"DEFAULT_PEDTYPE"`), which every
    untyped `<vehicle>`/`<person>` already uses — confirmed for real (via a real `sumo`
    invocation) that this correctly overrides the default without needing to touch every
    individual element, and that the inserted `vType` needs its own explicit `vClass`
    too: SUMO defaults an unspecified `vType`'s `vClass` to `"passenger"` regardless of
    its id — a real warning ("implicitly uses unsuitable vClass 'passenger'") was hit for
    pedestrians before `default_vclass` was added here.
    """
    extra = f' color="{color}"'
    if max_speed is not None:
        extra += f' maxSpeed="{max_speed}"'

    content = route_file.read_text(encoding="utf-8")
    if 'vType id="' in content:
        content = re.sub(
            r'(<vType id="[^"]*"[^/]*)/>',
            rf"\1{extra}/>",
            content,
            count=1,
        )
    else:
        content = re.sub(
            r"(<routes[^>]*>)",
            rf'\1\n    <vType id="{default_type_id}" vClass="{default_vclass}"{extra}/>',
            content,
            count=1,
        )
    route_file.write_text(content, encoding="utf-8")


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
    result = _run_random_trips(
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
    _customize_vtype(
        result, CAR_COLOR, default_type_id="DEFAULT_VEHTYPE", default_vclass="passenger"
    )
    return result


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
    result = _run_random_trips(
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
    # randomTrips.py already generates a <vType> here (--vehicle-class); customise it in
    # place — default_type_id/default_vclass are unused in that path but required by the
    # shared helper's signature. max_speed: SUMO's own default bicycle cap (~22 km/h,
    # confirmed for real via tripinfo-output) already looked reasonable on average, but
    # the project owner watched it in sumo-gui and asked for a clearer, more deliberate
    # gap from car speed (cars averaged ~34 km/h in the same real check) — an explicit,
    # lower cap here, not a config left to SUMO's own implicit default.
    _customize_vtype(
        result,
        BICYCLE_COLOR,
        default_type_id="DEFAULT_VEHTYPE",
        default_vclass="bicycle",
        max_speed=BICYCLE_MAX_SPEED,
    )
    return result


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
    result = _run_random_trips(
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
    _customize_vtype(
        result,
        PEDESTRIAN_COLOR,
        default_type_id="DEFAULT_PEDTYPE",
        default_vclass="pedestrian",
    )
    return result


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
