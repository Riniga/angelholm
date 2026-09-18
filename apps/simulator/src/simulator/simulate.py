"""Run a SUMO simulation from a `.sumocfg`."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class SimulationError(RuntimeError):
    """Raised when running the SUMO simulation fails."""


def run_headless(config_path: Path) -> None:
    """Run the simulation headlessly (`sumo -c <config>`) to completion.

    Raises `SimulationError` if the simulation exits non-zero — the automatable half of
    MVP-001's acceptance criteria. Visual verification via `sumo-gui` is a separate, manual
    step this function does not attempt.
    """
    logger.info("Running headless simulation: %s", config_path)
    result = subprocess.run(
        ["sumo", "-c", str(config_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SimulationError(
            f"sumo failed (exit {result.returncode}): {result.stderr.strip()}"
        )
    logger.info("Simulation completed successfully")


def run_gui(config_path: Path, gui_settings_file: Path | None = None) -> None:
    """Launch `sumo-gui` for interactive, visual observation of the simulation.

    `gui_settings_file`, when given (e.g. MVP-003's map-context background), is passed as
    `--gui-settings-file` — display-only, has no effect on `run_headless()`, which never
    receives it.

    Blocks until the GUI window is closed. Does not raise on a non-zero exit — closing the
    window is a normal, expected way for this to end, not a failure to surface.
    """
    logger.info("Launching sumo-gui: %s", config_path)
    command = ["sumo-gui", "-c", str(config_path)]
    if gui_settings_file is not None:
        command += ["--gui-settings-file", str(gui_settings_file)]
    subprocess.run(command, check=False)
