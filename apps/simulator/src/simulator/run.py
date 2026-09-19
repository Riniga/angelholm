"""Documented, repeatable entrypoint: build (if needed) and run the live Ängelholm
simulation, covering the area outlined in docs/architecture/mapoutline.png (MVP-002).

Since MVP-005 the city starts empty at 05:00 and individuals are spawned live through TraCI
until the run is stopped — there are no pre-generated route files any more.

Installed as the `simulator` console command (`pip install -e apps/simulator`):

    simulator                    # launch sumo-gui, reusing the committed network; runs
                                 # until you close the window
    simulator --headless         # no GUI; runs until interrupted (Ctrl+C)
    simulator --headless --max-seconds 600   # stop after 600 simulated seconds
    simulator --seed 1           # reproducible pattern for debugging
    simulator --stats my.json    # use another demand statistics file
    simulator --rebuild-network  # re-fetch OSM data and rebuild the network first
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from simulator.agents import Mode
from simulator.context_features import write_gui_settings
from simulator.demand import DEFAULT_DEMAND_JSON, DemandProfileError
from simulator.engine import EngineStats, run_live
from simulator.network import build_network, fetch_osm_extract, load_boundary_polygon

logger = logging.getLogger(__name__)

# apps/simulator/src/simulator/run.py -> apps/simulator/data
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _log_summary(stats: EngineStats) -> None:
    for mode in Mode:
        logger.info(
            "%s: spawned %d, arrived %d, skipped %d (no route)",
            mode.value,
            stats.spawned[mode],
            stats.arrived[mode],
            stats.skipped[mode],
        )
    logger.info("Peak concurrent travellers: %d", stats.peak_active)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the simulation pipeline. Returns a process exit code."""
    parser = argparse.ArgumentParser(
        description="Run the Ängelholm traffic simulation."
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without the GUI (for automation/CI).",
    )
    parser.add_argument(
        "--rebuild-network",
        action="store_true",
        help="Re-fetch OSM data and rebuild the network instead of reusing the "
        "committed one.",
    )
    parser.add_argument(
        "--max-seconds",
        type=float,
        default=None,
        help="Stop after this many simulated seconds. Default: run until stopped.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed the random spawning (patterns, not exact individuals, are what "
        "matters; useful for debugging). Default: different every run.",
    )
    parser.add_argument(
        "--stats",
        type=Path,
        default=DEFAULT_DEMAND_JSON,
        help="Demand statistics file: trips per day, hourly profile, mode shares. "
        "Default: the committed apps/simulator/data/demand-statistics.json.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    net_file = DATA_DIR / "network.net.xml"
    if args.rebuild_network or not net_file.exists():
        osm_file = fetch_osm_extract(DATA_DIR)
        boundary_polygon = load_boundary_polygon(DATA_DIR / "coverage-outline.geojson")
        build_network(osm_file, net_file, boundary_polygon=boundary_polygon)

    # GUI-only: the map-context background is read by sumo-gui via --gui-settings-file,
    # never touched by the headless simulation engine, so it is skipped for --headless.
    gui_settings_file = None
    if not args.headless:
        gui_settings_file = write_gui_settings(
            net_file, DATA_DIR / "angelholm-guisettings.xml"
        )

    try:
        stats = run_live(
            net_file,
            headless=args.headless,
            gui_settings_file=gui_settings_file,
            seed=args.seed,
            max_sim_seconds=args.max_seconds,
            demand_file=args.stats,
        )
    except DemandProfileError as error:
        logger.error("Invalid demand statistics: %s", error)
        return 1
    _log_summary(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
