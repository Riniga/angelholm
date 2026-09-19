"""Tests for simulator.context_features — pure file I/O + sumolib, no subprocess calls,
against a small hand-built net.xml fixture. Deterministic and offline.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from simulator.context_features import (
    CLOCK_TEXT_SIZE,
    DEFAULT_BACKGROUND_IMAGE,
    MANUAL_ROTATION,
    PEDESTRIAN_EXAGGERATION,
    ContextFeatureError,
    _read_net_bbox,
    write_gui_settings,
)

# A minimal net.xml: no edges, just enough for sumolib to read its <location> (bbox +
# projection). convBoundary is a plain 0,0 - 100,100 square in net-XY.
_MINIMAL_NET_XML = """<?xml version="1.0" encoding="UTF-8"?>
<net version="1.20">
    <location netOffset="0.00,0.00" convBoundary="0.00,0.00,100.00,100.00"
        origBoundary="10.51,0.0,10.52,0.0009"
        projParameter="+proj=utm +zone=33 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"/>
</net>
"""


class TestReadNetBbox:
    def test_reads_conv_boundary(self, tmp_path: Path) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")

        assert _read_net_bbox(net_file) == (0.0, 0.0, 100.0, 100.0)

    def test_missing_location_raises_context_feature_error(
        self, tmp_path: Path
    ) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text('<?xml version="1.0"?>\n<net version="1.20"/>\n')

        with pytest.raises(ContextFeatureError, match="no <location"):
            _read_net_bbox(net_file)


class TestWriteGuiSettings:
    def test_writes_decal_pointing_at_the_image(self, tmp_path: Path) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
        image_path = tmp_path / "context-background.png"
        image_path.write_bytes(b"")
        output_path = tmp_path / "gui-settings.xml"

        result = write_gui_settings(net_file, output_path, image_path=image_path)

        assert result == output_path
        content = output_path.read_text(encoding="utf-8")
        assert "<decal" in content
        assert 'file="context-background.png"' in content
        # Exact placement depends on the real IMAGE_NW_LAT_LON/IMAGE_SE_LAT_LON/MANUAL_*
        # constants and this fixture's own projection — just confirm numeric attributes
        # are present and well-formed, not their precise geographic values.
        for attribute in ("centerX", "centerY", "width", "height", "rotation"):
            assert f'{attribute}="' in content
        # rotation is applied as-is from MANUAL_ROTATION, not derived from the corners —
        # worth pinning down exactly, unlike the geometry-derived attributes above.
        assert f'rotation="{MANUAL_ROTATION}"' in content
        # MVP-004 Phase 5: pedestrians were hard to spot at normal size — confirmed
        # present, not just that *a* scheme exists.
        assert f'person_exaggeration="{PEDESTRIAN_EXAGGERATION}"' in content
        # MVP-006 Phase 5: the time-of-day label is a POI whose type text must be shown.
        assert 'poiType_show="1"' in content
        assert f'poiType_size="{CLOCK_TEXT_SIZE}"' in content

    def test_image_path_written_relative_to_settings_dir(self, tmp_path: Path) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text(_MINIMAL_NET_XML, encoding="utf-8")
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        image_path = data_dir / "context-background.png"
        image_path.write_bytes(b"")
        output_path = tmp_path / "config" / "gui-settings.xml"

        write_gui_settings(net_file, output_path, image_path=image_path)

        content = output_path.read_text(encoding="utf-8")
        assert "../data/context-background.png" in content.replace("\\", "/")

    def test_defaults_to_the_committed_background_image(self) -> None:
        # Checked via the signature, not by actually calling write_gui_settings(): a real
        # tmp_path fixture can land on a different drive than the repo on Windows, and
        # os.path.relpath() can't compute a relative path across drives — a test-only
        # concern (real callers always place output_path under the same DATA_DIR as the
        # image), not something worth working around in the function itself.
        default = inspect.signature(write_gui_settings).parameters["image_path"].default
        assert default == DEFAULT_BACKGROUND_IMAGE

    def test_missing_net_location_raises_context_feature_error(
        self, tmp_path: Path
    ) -> None:
        net_file = tmp_path / "test.net.xml"
        net_file.write_text('<?xml version="1.0"?>\n<net version="1.20"/>\n')
        output_path = tmp_path / "gui-settings.xml"

        with pytest.raises(ContextFeatureError, match="no <location"):
            write_gui_settings(net_file, output_path)
