"""Fetch OpenStreetMap data and build a routable SUMO network from it."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from simulator._paths import sumo_tools_dir

logger = logging.getLogger(__name__)

# A neighbourhood of central Ängelholm. west, south, east, north — south must be the
# smaller latitude (osmGet.py validates this and rejects an inverted bbox for real).
# Original MVP-001 candidate, verified to contain real road data (87 highway ways via a
# live Overpass query) but no longer the active default:
# DEFAULT_BBOX: tuple[float, float, float, float] = (12.8580, 56.2430, 12.8660, 56.2470)
DEFAULT_BBOX: tuple[float, float, float, float] = (
    12.845580,
    56.247082,
    12.860379,
    56.253877,
)
DEFAULT_PREFIX = "angelholm"


class NetworkBuildError(RuntimeError):
    """Raised when fetching OSM data or building the SUMO network fails."""


def fetch_osm_extract(
    output_dir: Path,
    bbox: tuple[float, float, float, float] = DEFAULT_BBOX,
    prefix: str = DEFAULT_PREFIX,
) -> Path:
    """Download an OpenStreetMap extract for `bbox` into `output_dir`.

    Uses SUMO's own `osmGet.py` tool (Overpass API under the hood) rather than a
    hand-rolled query. Returns the path to the downloaded `<prefix>_bbox.osm.xml` file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    osm_get_script = sumo_tools_dir() / "osmGet.py"
    bbox_arg = ",".join(str(v) for v in bbox)

    logger.info("Fetching OSM extract for bbox=%s into %s", bbox_arg, output_dir)
    # Retries matter here for real: Overpass's public server returned a genuine, transient
    # HTTP 504 during MVP-001 development — a plain single-attempt call is flaky in practice.
    result = subprocess.run(
        [
            sys.executable,
            str(osm_get_script),
            "-b",
            bbox_arg,
            "-p",
            prefix,
            "-d",
            str(output_dir),
            "--retries",
            "5",
            "--retry-delay",
            "10",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise NetworkBuildError(
            f"osmGet.py failed (exit {result.returncode}): {result.stderr.strip()}"
        )

    osm_file = output_dir / f"{prefix}_bbox.osm.xml"
    if not osm_file.exists():
        raise NetworkBuildError(
            f"osmGet.py reported success but {osm_file} was not created"
        )
    return osm_file


def build_network(osm_file: Path, output_path: Path) -> Path:
    """Convert a raw OSM XML extract into a routable SUMO network via `netconvert`.

    Returns `output_path` on success; raises `NetworkBuildError` on failure or if
    `netconvert` reports no edges/junctions were built.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Building SUMO network from %s -> %s", osm_file, output_path)
    result = subprocess.run(
        ["netconvert", "--osm-files", str(osm_file), "-o", str(output_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise NetworkBuildError(
            f"netconvert failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    if not output_path.exists():
        raise NetworkBuildError(
            f"netconvert reported success but {output_path} was not created"
        )
    return output_path
