"""Tests for simulator.run — mocked pipeline functions, no live SUMO/network calls."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

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
            patch("simulator.run.generate_traffic") as mock_traffic,
            patch("simulator.run.generate_bicycle_traffic") as mock_bikes,
            patch("simulator.run.generate_pedestrian_traffic") as mock_peds,
            patch("simulator.run.write_sumocfg") as mock_cfg,
            patch("simulator.run.run_gui") as mock_gui,
            patch("simulator.run.run_headless") as mock_headless,
        ):
            exit_code = main([])

        assert exit_code == 0
        mock_fetch.assert_not_called()
        mock_build.assert_not_called()
        mock_gui_settings.assert_called_once_with(
            tmp_path / "network.net.xml",
            tmp_path / "angelholm-guisettings.xml",
        )
        mock_traffic.assert_called_once_with(
            tmp_path / "network.net.xml", tmp_path / "angelholm.rou.xml"
        )
        mock_bikes.assert_called_once_with(
            tmp_path / "network.net.xml", tmp_path / "angelholm.bikes.rou.xml"
        )
        mock_peds.assert_called_once_with(
            tmp_path / "network.net.xml", tmp_path / "angelholm.peds.rou.xml"
        )
        mock_cfg.assert_called_once_with(
            tmp_path / "network.net.xml",
            tmp_path / "angelholm.rou.xml",
            tmp_path / "angelholm.sumocfg",
            additional_route_files=[
                tmp_path / "angelholm.bikes.rou.xml",
                tmp_path / "angelholm.peds.rou.xml",
            ],
        )
        mock_gui.assert_called_once_with(
            tmp_path / "angelholm.sumocfg",
            gui_settings_file=tmp_path / "angelholm-guisettings.xml",
        )
        mock_headless.assert_not_called()

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
            patch(
                "simulator.run.write_gui_settings",
                return_value=tmp_path / "angelholm-guisettings.xml",
            ),
            patch("simulator.run.generate_traffic"),
            patch("simulator.run.generate_bicycle_traffic"),
            patch("simulator.run.generate_pedestrian_traffic"),
            patch("simulator.run.write_sumocfg"),
            patch("simulator.run.run_gui"),
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
            patch(
                "simulator.run.write_gui_settings",
                return_value=tmp_path / "angelholm-guisettings.xml",
            ),
            patch("simulator.run.generate_traffic"),
            patch("simulator.run.generate_bicycle_traffic"),
            patch("simulator.run.generate_pedestrian_traffic"),
            patch("simulator.run.write_sumocfg"),
            patch("simulator.run.run_gui"),
        ):
            main(["--rebuild-network"])

        mock_fetch.assert_called_once()
        mock_build.assert_called_once()

    def test_headless_flag_runs_headless_not_gui_and_skips_gui_settings(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        monkeypatch.setattr("simulator.run.DATA_DIR", tmp_path)
        (tmp_path / "network.net.xml").write_text("<net/>")

        with (
            patch("simulator.run.fetch_osm_extract"),
            patch("simulator.run.build_network"),
            patch("simulator.run.write_gui_settings") as mock_gui_settings,
            patch("simulator.run.generate_traffic"),
            patch("simulator.run.generate_bicycle_traffic") as mock_bikes,
            patch("simulator.run.generate_pedestrian_traffic") as mock_peds,
            patch("simulator.run.write_sumocfg"),
            patch("simulator.run.run_gui") as mock_gui,
            patch("simulator.run.run_headless") as mock_headless,
        ):
            exit_code = main(["--headless"])

        assert exit_code == 0
        mock_headless.assert_called_once()
        mock_gui.assert_not_called()
        # Map context is a sumo-gui-only background — skipped entirely for --headless.
        mock_gui_settings.assert_not_called()
        # Bicycle/pedestrian traffic still generates for --headless (unlike the GUI
        # background) — only the map-context pipeline is GUI-only, not multimodal traffic.
        mock_bikes.assert_called_once()
        mock_peds.assert_called_once()
