"""Tests for simulator.simulate — mocked subprocess calls, no live SUMO invocation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from simulator.simulate import SimulationError, run_gui, run_headless


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="", stderr=stderr
    )


class TestRunHeadless:
    def test_success_returns_none(self, tmp_path: Path) -> None:
        config_path = tmp_path / "sim.sumocfg"
        with patch(
            "simulator.simulate.subprocess.run", return_value=_completed(0)
        ) as mock_run:
            assert run_headless(config_path) is None
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == ["sumo", "-c", str(config_path)]

    def test_nonzero_exit_raises_simulation_error(self, tmp_path: Path) -> None:
        config_path = tmp_path / "sim.sumocfg"
        with patch(
            "simulator.simulate.subprocess.run",
            return_value=_completed(1, "bad config"),
        ):
            with pytest.raises(SimulationError, match="sumo failed"):
                run_headless(config_path)


class TestRunGui:
    def test_launches_sumo_gui_with_config(self, tmp_path: Path) -> None:
        config_path = tmp_path / "sim.sumocfg"
        with patch(
            "simulator.simulate.subprocess.run", return_value=_completed(0)
        ) as mock_run:
            assert run_gui(config_path) is None
        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == ["sumo-gui", "-c", str(config_path)]

    def test_nonzero_exit_does_not_raise(self, tmp_path: Path) -> None:
        # Closing the GUI window is a normal way for this to end — must not be treated
        # as a failure the way run_headless's non-zero exit is.
        config_path = tmp_path / "sim.sumocfg"
        with patch(
            "simulator.simulate.subprocess.run", return_value=_completed(1, "closed")
        ):
            assert run_gui(config_path) is None
