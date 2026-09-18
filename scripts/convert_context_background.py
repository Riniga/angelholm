"""Convert `docs/architecture/map_plain.gif` into the committed
`apps/simulator/data/context-background.png` used as MVP-003's `sumo-gui` background.

A one-off (re-runnable) tool, not part of the `simulator` package: the project owner's
basemap screenshot only needs converting once, and again if they ever replace the source
image. `simulator.context_features.write_gui_settings()` places the resulting PNG using
its own known corner coordinates (`IMAGE_NW_LAT_LON`/`IMAGE_SE_LAT_LON`), not anything
computed here.

Usage:
    python scripts/convert_context_background.py
"""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_IMAGE = REPO_ROOT / "docs" / "architecture" / "map_plain.gif"
OUTPUT_IMAGE = REPO_ROOT / "apps" / "simulator" / "data" / "context-background.png"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    image = Image.open(SOURCE_IMAGE).convert("RGB")
    OUTPUT_IMAGE.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT_IMAGE)
    logger.info("Wrote %s (%dx%d)", OUTPUT_IMAGE, *image.size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
