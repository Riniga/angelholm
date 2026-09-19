"""Documented, repeatable entrypoint: build (if needed) and run the Ängelholm traffic
simulation, covering the area outlined in docs/architecture/mapoutline.png (MVP-002; grown
from MVP-001's original, smaller neighbourhood extract).

Installed as the `simulator` console command (`pip install -e apps/simulator`):

    simulator                  # launch sumo-gui, reusing the committed network
    simulator --headless       # run headlessly (no GUI), e.g. for automation
    simulator --rebuild-network  # re-fetch OSM data and rebuild the network first
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from simulator.context_features import write_gui_settings
from simulator.network import build_network, fetch_osm_extract, load_boundary_polygon
from simulator.simulate import run_gui, run_headless
from simulator.traffic import (
    generate_bicycle_traffic,
    generate_pedestrian_traffic,
    generate_traffic,
    write_sumocfg,
)

logger = logging.getLogger(__name__)

# apps/simulator/src/simulator/run.py -> apps/simulator/data
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


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
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    net_file = DATA_DIR / "network.net.xml"
    if args.rebuild_network or not net_file.exists():
        osm_file = fetch_osm_extract(DATA_DIR)
        boundary_polygon = load_boundary_polygon(DATA_DIR / "coverage-outline.geojson")
        build_network(osm_file, net_file, boundary_polygon=boundary_polygon)

    route_file = DATA_DIR / "angelholm.rou.xml"
    bicycle_route_file = DATA_DIR / "angelholm.bikes.rou.xml"
    pedestrian_route_file = DATA_DIR / "angelholm.peds.rou.xml"
    config_file = DATA_DIR / "angelholm.sumocfg"
    generate_traffic(net_file, route_file)
    generate_bicycle_traffic(net_file, bicycle_route_file)
    generate_pedestrian_traffic(net_file, pedestrian_route_file)
    write_sumocfg(
        net_file,
        route_file,
        config_file,
        additional_route_files=[bicycle_route_file, pedestrian_route_file],
    )

    if args.headless:
        run_headless(config_file)
    else:
        # GUI-only: the map-context background is read by sumo-gui via
        # --gui-settings-file, never touched by the headless simulation engine, so this
        # is skipped entirely for --headless.
        gui_settings_file = write_gui_settings(
            net_file, DATA_DIR / "angelholm-guisettings.xml"
        )
        run_gui(config_file, gui_settings_file=gui_settings_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
