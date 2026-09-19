"""Tests for simulator.run — mocked pipeline functions, no live SUMO/network calls."""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

from simulator.engine import EngineStats
from simulator.run import main


class TestMain:
    def test_reuses_existing_network_and_launches_gui_by_default(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.setattr("simulator.run.DATA_DIR", tmp_path)
        (tmp_path / "network.net.xml").write_text("<net/>")

        with (
            patch("simulator.run.fetch_osm_extract") as mock_fetch,
            patch("simulator.run.build_network") as mock_build,
            patch(
                "simulator.run.write_gui_settings",
                return_value=tmp_path / "angelholm-guisettings.xml",
            ) as mock_gui_settings,
            patch("simulator.run.run_live", return_value=EngineStats()) as mock_live,
        ):
            exit_code = main([])

        assert exit_code == 0
        mock_fetch.assert_not_called()
        mock_build.assert_not_called()
        mock_gui_settings.assert_called_once_with(
            tmp_path / "network.net.xml",
            tmp_path / "angelholm-guisettings.xml",
        )
        mock_live.assert_called_once_with(
            tmp_path / "network.net.xml",
            headless=False,
            gui_settings_file=tmp_path / "angelholm-guisettings.xml",
            seed=None,
            max_sim_seconds=None,
        )

    def test_missing_network_triggers_fetch_and_build_even_without_flag(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.setattr("simulator.run.DATA_DIR", tmp_path)
        # No network.net.xml created — must be built before anything else.

        with (
            patch(
                "simulator.run.fetch_osm_extract",
                return_value=tmp_path / "extract.osm.xml",
            ) as mock_fetch,
            patch(
                "simulator.run.load_boundary_polygon", return_value="1,2,3,4,1,2"
            ) as mock_load_polygon,
            patch("simulator.run.build_network") as mock_build,
            patch("simulator.run.write_gui_settings"),
            patch("simulator.run.run_live", return_value=EngineStats()),
        ):
            main([])

        mock_fetch.assert_called_once()
        mock_load_polygon.assert_called_once_with(tmp_path / "coverage-outline.geojson")
        mock_build.assert_called_once_with(
            tmp_path / "extract.osm.xml",
            tmp_path / "network.net.xml",
            boundary_polygon="1,2,3,4,1,2",
        )

    def test_rebuild_network_flag_forces_fetch_and_build(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.setattr("simulator.run.DATA_DIR", tmp_path)
        (tmp_path / "network.net.xml").write_text("<net/>")  # already exists

        with (
            patch(
                "simulator.run.fetch_osm_extract",
                return_value=tmp_path / "extract.osm.xml",
            ) as mock_fetch,
            patch("simulator.run.load_boundary_polygon", return_value="1,2,3,4,1,2"),
            patch("simulator.run.build_network") as mock_build,
            patch("simulator.run.write_gui_settings"),
            patch("simulator.run.run_live", return_value=EngineStats()),
        ):
            main(["--rebuild-network"])

        mock_fetch.assert_called_once()
        mock_build.assert_called_once()

    def test_headless_runs_without_gui_and_skips_gui_settings(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.setattr("simulator.run.DATA_DIR", tmp_path)
        (tmp_path / "network.net.xml").write_text("<net/>")

        with (
            patch("simulator.run.write_gui_settings") as mock_gui_settings,
            patch("simulator.run.run_live", return_value=EngineStats()) as mock_live,
        ):
            exit_code = main(["--headless"])

        assert exit_code == 0
        # Map context is a sumo-gui-only background — skipped entirely for --headless.
        mock_gui_settings.assert_not_called()
        mock_live.assert_called_once_with(
            tmp_path / "network.net.xml",
            headless=True,
            gui_settings_file=None,
            seed=None,
            max_sim_seconds=None,
        )

    def test_seed_and_max_seconds_are_passed_through(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.setattr("simulator.run.DATA_DIR", tmp_path)
        (tmp_path / "network.net.xml").write_text("<net/>")

        with patch("simulator.run.run_live", return_value=EngineStats()) as mock_live:
            main(["--headless", "--seed", "7", "--max-seconds", "600"])

        kwargs = mock_live.call_args.kwargs
        assert kwargs["seed"] == 7
        assert kwargs["max_sim_seconds"] == 600.0

    def test_logs_a_summary_of_what_happened(
        self, tmp_path: Path, monkeypatch, caplog
    ) -> None:
        monkeypatch.setattr("simulator.run.DATA_DIR", tmp_path)
        (tmp_path / "network.net.xml").write_text("<net/>")
        stats = EngineStats(peak_active=42)

        with (
            patch("simulator.run.run_live", return_value=stats),
            caplog.at_level(logging.INFO, logger="simulator.run"),
        ):
            main(["--headless"])

        assert "car: spawned 0" in caplog.text
        assert "pedestrian: spawned 0" in caplog.text
        assert "Peak concurrent travellers: 42" in caplog.text
