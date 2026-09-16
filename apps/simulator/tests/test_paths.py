"""Tests for simulator._paths — real lookup against the installed eclipse-sumo package,
not mocked: this is a pure path computation with no network/subprocess involved.
"""

from __future__ import annotations

from simulator._paths import sumo_tools_dir


class TestSumoToolsDir:
    def test_returns_existing_directory_with_expected_tools(self) -> None:
        tools_dir = sumo_tools_dir()
        assert tools_dir.is_dir()
        assert (tools_dir / "osmGet.py").exists()
        assert (tools_dir / "randomTrips.py").exists()
