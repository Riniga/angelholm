"""Generate non-routing map context shapes (water, land use) for `sumo-gui` display.

Uses SUMO's own `polyconvert` tool against the same OSM extract `network.py` already
fetches. Purely visual — the headless `sumo` simulation engine never reads these shapes,
so this module has no effect on routing, traffic generation, or simulation output. See
`docs/architecture/decisions/ADR-008-polyconvert-for-context-features.md`.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# apps/simulator/src/simulator/context_features.py -> apps/simulator/data
DEFAULT_TYPE_FILE = (
    Path(__file__).resolve().parents[2] / "data" / "context-features.typ.xml"
)


class ContextFeatureError(RuntimeError):
    """Raised when generating map context shapes fails."""


def build_context_features(
    osm_file: Path,
    net_file: Path,
    output_path: Path,
    type_file: Path = DEFAULT_TYPE_FILE,
) -> Path:
    """Convert `osm_file` into a `.poly.xml` shapes file via `polyconvert`.

    `net_file` supplies the coordinate offset/projection to align shapes with the built
    network. `type_file` restricts the imported shapes to water/land-use categories
    (`--discard` drops any OSM type not listed in it) rather than SUMO's much broader
    bundled default, which also imports buildings and amenities.

    Returns `output_path` on success; raises `ContextFeatureError` on failure or if
    `polyconvert` reports no output file was created.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Building context features from %s -> %s", osm_file, output_path)
    result = subprocess.run(
        [
            "polyconvert",
            "--net-file",
            str(net_file),
            "--osm-files",
            str(osm_file),
            "--type-file",
            str(type_file),
            "--discard",
            "-o",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ContextFeatureError(
            f"polyconvert failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    if not output_path.exists():
        raise ContextFeatureError(
            f"polyconvert reported success but {output_path} was not created"
        )
    return output_path
