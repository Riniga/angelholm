"""Shared path helper for locating SUMO's own bundled tools."""

from __future__ import annotations

from pathlib import Path


def sumo_tools_dir() -> Path:
    """Locate the `tools/` directory bundled with the installed `eclipse-sumo` package."""
    import sumo

    return Path(sumo.__file__).parent / "tools"
