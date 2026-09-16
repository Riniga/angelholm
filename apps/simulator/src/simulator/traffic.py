"""Generate synthetic vehicle traffic over a SUMO network and its simulation config."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

MIN_VEHICLES = 10
DEFAULT_BEGIN = 0
DEFAULT_END = 200
DEFAULT_PERIOD = 15.0
# Fixed, not random — matches the "Scenarios Should Be Reproducible" architectural
# principle (docs/architecture/overview.md): the same inputs must produce the same traffic.
DEFAULT_SEED = 42


class TrafficGenerationError(RuntimeError):
    """Raised when generating traffic or writing the simulation config fails."""


def _sumo_tools_dir() -> Path:
    """Locate the `tools/` directory bundled with the installed `eclipse-sumo` package."""
    import sumo

    return Path(sumo.__file__).parent / "tools"


def generate_traffic(
    net_file: Path,
    route_file: Path,
    *,
    begin: int = DEFAULT_BEGIN,
    end: int = DEFAULT_END,
    period: float = DEFAULT_PERIOD,
    seed: int = DEFAULT_SEED,
) -> Path:
    """Generate random, routed vehicle trips over `net_file` via SUMO's `randomTrips.py`.

    Deterministic (fixed `seed`) for reproducibility. Raises `TrafficGenerationError` if
    fewer than `MIN_VEHICLES` vehicles end up in the resulting route file.
    """
    route_file.parent.mkdir(parents=True, exist_ok=True)
    random_trips_script = _sumo_tools_dir() / "randomTrips.py"
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
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise TrafficGenerationError(
            f"randomTrips.py failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    if not route_file.exists():
        raise TrafficGenerationError(
            f"randomTrips.py reported success but {route_file} was not created"
        )

    vehicle_count = route_file.read_text(encoding="utf-8").count("<vehicle ")
    if vehicle_count < MIN_VEHICLES:
        raise TrafficGenerationError(
            f"Only {vehicle_count} vehicles generated, need at least {MIN_VEHICLES}"
        )
    logger.info("Generated %d vehicles over %s", vehicle_count, net_file)
    return route_file


def write_sumocfg(
    net_file: Path,
    route_file: Path,
    config_path: Path,
    *,
    begin: int = DEFAULT_BEGIN,
    end: int = DEFAULT_END,
) -> Path:
    """Write a `.sumocfg` tying `net_file` and `route_file` together.

    Paths are written relative to `config_path`'s own directory, since that's how SUMO
    resolves them at run time — the three files don't have to live in the same directory.
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    net_rel = os.path.relpath(net_file, start=config_path.parent)
    route_rel = os.path.relpath(route_file, start=config_path.parent)
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
</configuration>
""",
        encoding="utf-8",
    )
    return config_path
