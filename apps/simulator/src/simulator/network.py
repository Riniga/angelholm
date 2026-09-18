"""Fetch OpenStreetMap data and build a routable SUMO network from it."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from shapely.geometry import shape

from simulator._paths import sumo_tools_dir

logger = logging.getLogger(__name__)

# MVP-002: the outlined central-Ängelholm coverage area (docs/mvp/002-extended-map-area.md,
# docs/architecture/mapoutline.png). west, south, east, north — south must be the smaller
# latitude (osmGet.py validates this and rejects an inverted bbox for real, as MVP-001 hit
# once already). This is the outline's bounding box; the outline itself is not a rectangle
# — see load_boundary_polygon() / build_network()'s boundary_polygon for the actual clip.
#
# MVP-001's original, smaller neighbourhood extract, no longer the active default:
# DEFAULT_BBOX: tuple[float, float, float, float] = (12.845580, 56.247082, 12.860379, 56.253877)
DEFAULT_BBOX: tuple[float, float, float, float] = (
    12.849519,
    56.225986,
    12.894902,
    56.255099,
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


def load_boundary_polygon(geojson_path: Path) -> str:
    """Read a single-`Polygon`-feature GeoJSON file and return its ring as the flat
    `"lon0,lat0,lon1,lat1,..."` string `netconvert --keep-edges.in-geo-boundary` expects.

    Used to clip the built network to the project owner's hand-drawn coverage outline
    (`docs/architecture/mapoutline.png`, digitized by `scripts/extract_coverage_outline.py`)
    rather than just `DEFAULT_BBOX`'s rectangle — see ADR-007.
    """
    feature = json.loads(geojson_path.read_text(encoding="utf-8"))
    polygon = shape(feature["geometry"])
    exterior_coords = polygon.exterior.coords
    return ",".join(f"{lon},{lat}" for lon, lat in exterior_coords)


def build_network(
    osm_file: Path,
    output_path: Path,
    boundary_polygon: str | None = None,
) -> Path:
    """Convert a raw OSM XML extract into a routable SUMO network via `netconvert`.

    When `boundary_polygon` is given (a `"lon0,lat0,lon1,lat1,..."` string, e.g. from
    `load_boundary_polygon()`), edges outside that outline are dropped via
    `--keep-edges.in-geo-boundary`, on top of whatever bbox the OSM extract itself covers.
    `--output.street-names` carries real OSM street names onto edges (purely additive
    metadata — MVP-004 needs it to identify real, named entry/exit roads by hand rather
    than guessing from edge IDs; does not affect edge/junction counts or topology).

    Returns `output_path` on success; raises `NetworkBuildError` on failure or if
    `netconvert` reports no edges/junctions were built.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "netconvert",
        "--osm-files",
        str(osm_file),
        "-o",
        str(output_path),
        "--output.street-names",
    ]
    if boundary_polygon is not None:
        command += ["--keep-edges.in-geo-boundary", boundary_polygon]

    logger.info("Building SUMO network from %s -> %s", osm_file, output_path)
    result = subprocess.run(
        command,
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
