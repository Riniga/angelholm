"""Place a real basemap image behind the network in `sumo-gui` for visual context.

`sumo-gui` only ever draws the road network's own geometry — it has no notion of water,
parks, or built-up areas. `docs/architecture/map_plain.gif` (the project owner's own
basemap screenshot, converted once to `apps/simulator/data/context-background.png`) is
shown as a georeferenced background ("decal") behind the network, purely so a human
watching the simulation recognises the area. Purely visual: headless `sumo` never reads
view-settings files, so this module has no effect on routing, traffic generation, or
simulation output. See
`docs/architecture/decisions/ADR-008-basemap-image-for-context-features.md`.

An earlier version of this module rendered water/land-use shapes from raw OSM data via
`polyconvert` — abandoned after a real defect was found: `polyconvert` can only keep or
discard a whole shape, never clip its geometry, so a large coastal water body leaked in far
outside the coverage area. Using the project owner's own complete, already-correct basemap
image sidesteps that whole class of problem.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import defusedxml.ElementTree as ET
import sumolib

logger = logging.getLogger(__name__)

# apps/simulator/src/simulator/context_features.py -> apps/simulator/data
DEFAULT_BACKGROUND_IMAGE = (
    Path(__file__).resolve().parents[2] / "data" / "context-background.png"
)

# docs/architecture/map_plain.gif's own corners, as given by the project owner — pixel
# (0, 0) is the NW corner, pixel (width, height) is the SE corner.
IMAGE_NW_LAT_LON = (56.255790, 12.833104)
IMAGE_SE_LAT_LON = (56.224411, 12.907042)

# The geographic corners above placed the image close, but not pixel-perfect — expected,
# since they come from reading a screenshot's edges, not a survey. Corrected by hand,
# 2026-09-18: the project owner used sumo-gui's own built-in decal editor (view settings ->
# Background) to nudge the image live, read back its resulting centerX/centerY/width/height/
# rotation, and these are that correction relative to the geographic-corner computation
# below (not absolute net-XY values), so they stay valid if the network is ever rebuilt at
# a different offset. Re-derive by repeating that process if the background image itself
# ever changes.
MANUAL_OFFSET_X = -21.648822874034522
MANUAL_OFFSET_Y = 4.4780025142244995
MANUAL_SCALE_X = 1.0197715118404214
MANUAL_SCALE_Y = 0.9542362298774799
MANUAL_ROTATION = -2.0

# MVP-004 Phase 5: even with an explicit, distinct colour (simulator.agents), pedestrians
# were still hard to spot at normal size against a busy city network — confirmed for real
# by the project owner in sumo-gui. `person_exaggeration`/`"given person/type color"` are
# real sumo-gui view-settings attributes, confirmed from SUMO's own bundled
# tools/game/hiking/view.xml example (a pedestrian-focused game mode), not guessed.
PEDESTRIAN_EXAGGERATION = 5.0

# MVP-006 Phase 5: the simulated time of day is drawn as the "type" text of a POI that
# `simulator.engine` keeps in the view corner (sumo-gui's own toolbar clock clips the hour).
# `poiType_show`/`poiType_size`/`poiType_color` are real view-settings attributes, confirmed
# for real by a run in sumo-gui (a red label appeared), not guessed. Size in sumo-gui's own
# text units; tuned by eye.
CLOCK_TEXT_SIZE = 60


class ContextFeatureError(RuntimeError):
    """Raised when placing the map context background fails."""


def _read_net_bbox(net_file: Path) -> tuple[float, float, float, float]:
    """Read `(min_x, min_y, max_x, max_y)` from a `.net.xml`'s own `<location>` element."""
    location = ET.parse(net_file).getroot().find("location")
    if location is None or location.get("convBoundary") is None:
        raise ContextFeatureError(f"{net_file} has no <location convBoundary=.../>")
    min_x, min_y, max_x, max_y = (
        float(v) for v in location.get("convBoundary", "").split(",")
    )
    return min_x, min_y, max_x, max_y


def write_gui_settings(
    net_file: Path,
    output_path: Path,
    image_path: Path = DEFAULT_BACKGROUND_IMAGE,
) -> Path:
    """Write a `sumo-gui` view-settings XML with `image_path` as a georeferenced `<decal>`.

    Placement is computed from `IMAGE_NW_LAT_LON`/`IMAGE_SE_LAT_LON`, converted to
    `net_file`'s own coordinate system, then adjusted by the `MANUAL_*` constants above.
    GUI-only: headless `sumo` never reads view-settings files, so this has no effect on
    `simulator --headless`.
    """
    # _read_net_bbox() confirms net_file is a real, readable network before the (pricier)
    # full sumolib parse needed for the lon/lat -> XY conversion below.
    _read_net_bbox(net_file)
    net = sumolib.net.readNet(str(net_file))

    nw_x, nw_y = net.convertLonLat2XY(IMAGE_NW_LAT_LON[1], IMAGE_NW_LAT_LON[0])
    se_x, se_y = net.convertLonLat2XY(IMAGE_SE_LAT_LON[1], IMAGE_SE_LAT_LON[0])
    min_x, max_x = sorted((nw_x, se_x))
    min_y, max_y = sorted((nw_y, se_y))

    center_x = (min_x + max_x) / 2 + MANUAL_OFFSET_X
    center_y = (min_y + max_y) / 2 + MANUAL_OFFSET_Y
    width = (max_x - min_x) * MANUAL_SCALE_X
    height = (max_y - min_y) * MANUAL_SCALE_Y

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_rel = os.path.relpath(image_path, start=output_path.parent)
    output_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<viewsettings>
    <decal file="{image_rel}" centerX="{center_x}" centerY="{center_y}" width="{width}" height="{height}" rotation="{MANUAL_ROTATION}"/>
    <scheme name="angelholm">
        <vehicles vehicle_exaggeration="1.00">
            <colorScheme name="given vehicle/type/route color">
                <entry color="yellow"/>
            </colorScheme>
        </vehicles>
        <persons person_exaggeration="{PEDESTRIAN_EXAGGERATION}">
            <colorScheme name="given person/type color">
                <entry color="blue"/>
            </colorScheme>
        </persons>
        <pois poiType_show="1" poiType_size="{CLOCK_TEXT_SIZE}" poiType_color="red"/>
    </scheme>
</viewsettings>
""",
        encoding="utf-8",
    )
    logger.info("Wrote GUI settings %s", output_path)
    return output_path
