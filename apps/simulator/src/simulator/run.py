"""Documented, repeatable entrypoint: build (if needed) and run the first Ängelholm
traffic simulation (MVP-001).

Installed as the `simulator` console command (`pip install -e apps/simulator`):

    simulator                  # launch sumo-gui, reusing the committed network
    simulator --headless       # run headlessly (no GUI), e.g. for automation
    simulator --rebuild-network  # re-fetch OSM data and rebuild the network first
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from simulator.network import build_network, fetch_osm_extract
from simulator.simulate import run_gui, run_headless
from simulator.traffic import generate_traffic, write_sumocfg

logger = logging.getLogger(__name__)

# apps/simulator/src/simulator/run.py -> apps/simulator/data
DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the simulation pipeline. Returns a process exit code."""
    parser = argparse.ArgumentParser(
        description="Run the first Ängelholm traffic simulation (MVP-001)."
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
        build_network(osm_file, net_file)

    route_file = DATA_DIR / "angelholm.rou.xml"
    config_file = DATA_DIR / "angelholm.sumocfg"
    generate_traffic(net_file, route_file)
    write_sumocfg(net_file, route_file, config_file)

    if args.headless:
        run_headless(config_file)
    else:
        run_gui(config_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
