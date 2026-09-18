"""Extract the MVP-002 coverage outline from `docs/architecture/mapoutline.png` as GeoJSON.

The project owner drew a red outline over a map screenshot to mark the exact area MVP-002
should cover. This script is a one-off (re-runnable) tool, not part of the `simulator`
package: it isolates that hand-drawn outline by color, traces it as an ordered polygon,
converts pixel coordinates to lon/lat using the image's own known corner coordinates, and
writes the result as `docs/architecture/coverage-outline.geojson`, plus a debug overlay PNG
for a quick visual sanity check.

Usage:
    python scripts/extract_coverage_outline.py                  # full extraction
    python scripts/extract_coverage_outline.py --probe          # print sampled outline
                                                                  # colors, do nothing else
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import cv2
import numpy as np
from shapely.geometry import Polygon, mapping

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGE_PATH = REPO_ROOT / "docs" / "architecture" / "mapoutline.png"
GEOJSON_OUTPUT_PATH = REPO_ROOT / "docs" / "architecture" / "coverage-outline.geojson"
DEBUG_OVERLAY_PATH = REPO_ROOT / "docs" / "architecture" / "coverage-outline-check.png"

# The image's own corners, as given by the project owner — pixel (0, 0) is the NW corner,
# pixel (width, height) is the SE corner. (lat, lon), matching how the coordinates were
# given in conversation.
NW_LAT_LON = (56.255099, 12.849519)
SE_LAT_LON = (56.225986, 12.894902)

# BGR — sampled directly from the image (dominant color among reddish pixels; the next most
# common candidate colors are >100 counts lower and belong to the basemap's own orange/pink
# road tones, e.g. the route-107 shield). See docs/plans/002-extended-map-area.plan.md
# Phase 1, TODO 2.
OUTLINE_COLOR_BGR = np.array([21, 0, 136])
COLOR_DISTANCE_THRESHOLD = 40

# Douglas-Peucker simplification epsilon, as a fraction of the traced contour's perimeter.
SIMPLIFY_EPSILON_FRACTION = 0.002


def probe_outline_colors(image: np.ndarray, top_n: int = 15) -> None:
    """Print the most common colors among reddish pixels, to help pick/verify
    OUTLINE_COLOR_BGR. Reddish = red channel clearly higher than both blue and green."""
    b, g, r = (image[..., i].astype(int) for i in range(3))
    redness = r - np.maximum(b, g)
    candidate_mask = redness > 60
    colors = image[candidate_mask]
    if colors.size == 0:
        print("No reddish pixels found.")
        return
    unique_colors, counts = np.unique(colors.reshape(-1, 3), axis=0, return_counts=True)
    order = np.argsort(-counts)
    print(f"Top {top_n} candidate outline colors (BGR, pixel count):")
    for i in order[:top_n]:
        print(f"  {tuple(int(v) for v in unique_colors[i])}  {int(counts[i])}")


def extract_outline_contour(image: np.ndarray) -> np.ndarray:
    """Return the largest closed contour matching OUTLINE_COLOR_BGR, as an (N, 2) pixel
    array. Raises ValueError if no plausible contour is found."""
    distance = np.linalg.norm(image.astype(int) - OUTLINE_COLOR_BGR, axis=-1)
    mask = (distance < COLOR_DISTANCE_THRESHOLD).astype(np.uint8) * 255

    kernel = np.ones((3, 3), np.uint8)
    closed_mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        closed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contours:
        raise ValueError(
            "No contours found for the configured outline color — check "
            "OUTLINE_COLOR_BGR against a fresh --probe run."
        )

    largest = max(contours, key=cv2.contourArea)
    image_area = image.shape[0] * image.shape[1]
    if cv2.contourArea(largest) < 0.05 * image_area:
        raise ValueError(
            "Largest matching contour is implausibly small relative to the image — "
            "check OUTLINE_COLOR_BGR and COLOR_DISTANCE_THRESHOLD."
        )

    perimeter = cv2.arcLength(largest, True)
    epsilon = SIMPLIFY_EPSILON_FRACTION * perimeter
    simplified = cv2.approxPolyDP(largest, epsilon, True)
    return simplified.reshape(-1, 2)


def pixel_to_lonlat(
    px: float, py: float, image_width: int, image_height: int
) -> tuple[float, float]:
    """Convert an image pixel coordinate to (lon, lat) via linear interpolation between
    the image's known NW and SE corners. Accurate enough at this ~3 km scale — this is a
    visualization-scope outline, not a survey-grade boundary."""
    nw_lat, nw_lon = NW_LAT_LON
    se_lat, se_lon = SE_LAT_LON
    lon = nw_lon + (px / image_width) * (se_lon - nw_lon)
    lat = nw_lat + (py / image_height) * (se_lat - nw_lat)
    return lon, lat


def build_polygon(
    contour_px: np.ndarray, image_width: int, image_height: int
) -> Polygon:
    vertices_lonlat = [
        pixel_to_lonlat(px, py, image_width, image_height) for px, py in contour_px
    ]
    polygon = Polygon(vertices_lonlat)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)
    if polygon.is_empty or not polygon.is_valid:
        raise ValueError("Extracted polygon is invalid even after buffer(0) repair.")
    return polygon


def write_geojson(polygon: Polygon, output_path: Path) -> None:
    feature = {
        "type": "Feature",
        "properties": {
            "name": "MVP-002 coverage outline",
            "source": "docs/architecture/mapoutline.png",
        },
        "geometry": mapping(polygon),
    }
    output_path.write_text(json.dumps(feature, indent=2) + "\n", encoding="utf-8")
    logger.info("Wrote %s", output_path)


def write_debug_overlay(
    image: np.ndarray, contour_px: np.ndarray, output_path: Path
) -> None:
    overlay = image.copy()
    pts = contour_px.reshape(-1, 1, 2).astype(np.int32)
    cv2.polylines(overlay, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
    for px, py in contour_px:
        cv2.circle(overlay, (int(px), int(py)), 3, (255, 0, 0), -1)
    cv2.imwrite(str(output_path), overlay)
    logger.info("Wrote %s", output_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--probe",
        action="store_true",
        help="Print sampled outline colors and exit, without writing any output.",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    image = cv2.imread(str(IMAGE_PATH))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {IMAGE_PATH}")

    if args.probe:
        probe_outline_colors(image)
        return 0

    height, width = image.shape[:2]
    contour_px = extract_outline_contour(image)
    logger.info("Extracted polygon with %d vertices", len(contour_px))

    polygon = build_polygon(contour_px, width, height)
    logger.info("Polygon bounds (lon, lat): %s", polygon.bounds)
    logger.info(
        "Given corners: NW %s, SE %s — compare against the polygon bounds above.",
        NW_LAT_LON,
        SE_LAT_LON,
    )

    write_geojson(polygon, GEOJSON_OUTPUT_PATH)
    write_debug_overlay(image, contour_px, DEBUG_OVERLAY_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
