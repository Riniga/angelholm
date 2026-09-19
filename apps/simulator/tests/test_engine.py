"""Tests for simulator.engine — `traci` is mocked, no live SUMO invocation."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from traci.exceptions import FatalTraCIError, TraCIException

from simulator import engine
from simulator.agents import Individual, Mode
from simulator.demand import DEFAULT_DEMAND_JSON
from simulator.engine import (
    BICYCLE_TYPE_ID,
    MAX_SPAWN_ATTEMPTS,
    START_TIME,
    EngineStats,
    LiveEngine,
    SimulationError,
    _build_sumo_args,
    _rgba,
    format_clock,
    run_live,
)


class FakeSource:
    """A scripted `IndividualSource`: `due_by_time` maps sim time -> modes."""

    def __init__(self, due_by_time: dict[float, list[Mode]] | None = None) -> None:
        self._due_by_time = due_by_time or {}
        self.draws: list[Mode] = []

    def due(self, sim_time: float) -> list[Mode]:
        return self._due_by_time.get(sim_time, [])

    def draw(self, mode: Mode) -> Individual:
        self.draws.append(mode)
        return Individual(mode=mode, origin="a", destination="b")


def _route(*edges: str) -> SimpleNamespace:
    return SimpleNamespace(edges=edges)


@pytest.fixture
def traci_mock():
    with patch("simulator.engine.traci") as mock:
        mock.simulation.findRoute.return_value = _route("a", "b")
        mock.vehicle.getIDList.return_value = ()
        mock.person.getIDList.return_value = ()
        yield mock


def _clock(traci_mock, start: float = START_TIME) -> None:
    """Make `simulation.getTime()` advance by one second per `simulationStep()`."""
    state = {"t": start}

    def step() -> None:
        state["t"] += 1.0

    traci_mock.simulationStep.side_effect = step
    traci_mock.simulation.getTime.side_effect = lambda: state["t"]


class TestFormatClock:
    def test_start_of_run_is_five_o_clock(self) -> None:
        assert format_clock(START_TIME) == "05:00:00"

    def test_minutes_and_seconds(self) -> None:
        assert format_clock(START_TIME + 3725) == "06:02:05"

    def test_wraps_past_midnight(self) -> None:
        assert format_clock(86400 + 3600) == "01:00:00"


class TestRgba:
    def test_converts_unit_floats_to_0_255(self) -> None:
        assert _rgba("1,1,0") == (255, 255, 0, 255)
        assert _rgba("0,1,0") == (0, 255, 0, 255)


class TestStart:
    def test_starts_sumo_and_configures_vtypes(self, traci_mock) -> None:
        LiveEngine(FakeSource(), ["sumo", "-n", "x"]).start()

        traci_mock.start.assert_called_once_with(["sumo", "-n", "x"])
        traci_mock.vehicletype.copy.assert_called_once_with(
            "DEFAULT_VEHTYPE", BICYCLE_TYPE_ID
        )
        traci_mock.vehicletype.setVehicleClass.assert_called_once_with(
            BICYCLE_TYPE_ID, "bicycle"
        )
        traci_mock.vehicletype.setMaxSpeed.assert_called_once_with(
            BICYCLE_TYPE_ID, engine.BICYCLE_MAX_SPEED
        )
        colours = {
            call.args[0]: call.args[1]
            for call in traci_mock.vehicletype.setColor.call_args_list
        }
        assert colours["DEFAULT_VEHTYPE"] == (255, 255, 0, 255)
        assert colours[BICYCLE_TYPE_ID] == (0, 255, 0, 255)
        assert colours["DEFAULT_PEDTYPE"] == (255, 0, 255, 255)

    def test_start_failure_becomes_simulation_error(self, traci_mock) -> None:
        traci_mock.start.side_effect = FileNotFoundError("sumo")

        with pytest.raises(SimulationError, match="Could not start SUMO"):
            LiveEngine(FakeSource(), ["sumo"]).start()


class TestRouteFor:
    def test_returns_edges_when_a_route_exists(self, traci_mock) -> None:
        traci_mock.simulation.findRoute.return_value = _route("a", "m", "b")
        live = LiveEngine(FakeSource(), [])

        edges = live._route_for(Individual(Mode.BICYCLE, "a", "b"))

        assert edges == ["a", "m", "b"]
        traci_mock.simulation.findRoute.assert_called_once_with("a", "b", "bicycle_t")

    def test_returns_none_when_there_is_no_route(self, traci_mock) -> None:
        traci_mock.simulation.findRoute.return_value = _route()

        assert (
            LiveEngine(FakeSource(), [])._route_for(Individual(Mode.CAR, "a", "b"))
            is None
        )


class TestSpawn:
    def test_spawns_a_car_with_an_empty_route_then_set_route(self, traci_mock) -> None:
        live = LiveEngine(FakeSource(), [])

        assert live.spawn(Mode.CAR) is True

        traci_mock.vehicle.add.assert_called_once_with(
            "car_0", "", typeID="DEFAULT_VEHTYPE"
        )
        traci_mock.vehicle.setRoute.assert_called_once_with("car_0", ["a", "b"])
        traci_mock.route.add.assert_not_called()
        assert live.stats.spawned[Mode.CAR] == 1

    def test_spawns_a_bicycle_with_the_bicycle_type(self, traci_mock) -> None:
        live = LiveEngine(FakeSource(), [])

        live.spawn(Mode.BICYCLE)

        traci_mock.vehicle.add.assert_called_once_with(
            "bike_0", "", typeID=BICYCLE_TYPE_ID
        )

    def test_spawns_a_pedestrian_as_a_person_with_a_walking_stage(
        self, traci_mock
    ) -> None:
        live = LiveEngine(FakeSource(), [])

        live.spawn(Mode.PEDESTRIAN)

        traci_mock.person.add.assert_called_once_with(
            "ped_0", "a", 0, typeID="DEFAULT_PEDTYPE"
        )
        traci_mock.person.appendWalkingStage.assert_called_once_with(
            "ped_0", ["a", "b"], -1
        )
        traci_mock.vehicle.add.assert_not_called()

    def test_ids_increase_per_mode(self, traci_mock) -> None:
        live = LiveEngine(FakeSource(), [])

        live.spawn(Mode.CAR)
        live.spawn(Mode.CAR)

        ids = [call.args[0] for call in traci_mock.vehicle.add.call_args_list]
        assert ids == ["car_0", "car_1"]

    def test_retries_with_a_fresh_pair_when_there_is_no_route(self, traci_mock) -> None:
        traci_mock.simulation.findRoute.side_effect = [_route(), _route(), _route("a")]
        source = FakeSource()
        live = LiveEngine(source, [])

        assert live.spawn(Mode.CAR) is True

        assert len(source.draws) == 3
        assert live.stats.spawned[Mode.CAR] == 1
        assert live.stats.skipped[Mode.CAR] == 0

    def test_gives_up_and_counts_a_skip_after_max_attempts(self, traci_mock) -> None:
        traci_mock.simulation.findRoute.return_value = _route()
        source = FakeSource()
        live = LiveEngine(source, [])

        assert live.spawn(Mode.CAR) is False

        assert len(source.draws) == MAX_SPAWN_ATTEMPTS
        assert live.stats.skipped[Mode.CAR] == 1
        assert live.stats.spawned[Mode.CAR] == 0
        traci_mock.vehicle.add.assert_not_called()

    def test_rejected_add_counts_as_a_failed_attempt_not_a_crash(
        self, traci_mock
    ) -> None:
        traci_mock.vehicle.add.side_effect = [TraCIException("full"), None]
        live = LiveEngine(FakeSource(), [])

        assert live.spawn(Mode.CAR) is True

        assert traci_mock.vehicle.add.call_count == 2

    def test_rejected_walking_stage_removes_the_person_and_uses_a_fresh_id(
        self, traci_mock
    ) -> None:
        # Regression: a real run showed SUMO rejecting the walking stage ("Invalid
        # arrivalPos") after the person was added; the retry then hit "person ... already
        # exists" over and over because the id was reused and the person never removed.
        traci_mock.person.appendWalkingStage.side_effect = [
            TraCIException("Invalid arrivalPos"),
            None,
        ]
        live = LiveEngine(FakeSource(), [])

        assert live.spawn(Mode.PEDESTRIAN) is True

        traci_mock.person.remove.assert_called_once_with("ped_0")
        ids = [call.args[0] for call in traci_mock.person.add.call_args_list]
        assert ids == ["ped_0", "ped_1"]

    def test_failed_set_route_removes_the_half_added_vehicle(self, traci_mock) -> None:
        traci_mock.vehicle.setRoute.side_effect = [TraCIException("bad"), None]
        live = LiveEngine(FakeSource(), [])

        assert live.spawn(Mode.CAR) is True

        traci_mock.vehicle.remove.assert_called_once_with("car_0")


class TestStep:
    def test_spawns_only_what_the_source_says_is_due(self, traci_mock) -> None:
        _clock(traci_mock)
        source = FakeSource({START_TIME + 1: [Mode.CAR, Mode.PEDESTRIAN]})
        live = LiveEngine(source, [])

        live.step()

        assert source.draws == [Mode.CAR, Mode.PEDESTRIAN]
        traci_mock.vehicle.add.assert_called_once()
        traci_mock.person.add.assert_called_once()

    def test_step_returns_the_simulated_time(self, traci_mock) -> None:
        _clock(traci_mock)

        assert LiveEngine(FakeSource(), []).step() == START_TIME + 1

    def test_counts_active_per_mode_by_id_prefix(self, traci_mock) -> None:
        _clock(traci_mock)
        traci_mock.vehicle.getIDList.return_value = ("car_0", "car_1", "bike_0")
        traci_mock.person.getIDList.return_value = ("ped_0",)
        live = LiveEngine(FakeSource(), [])

        live.step()

        assert live.stats.active == {
            Mode.CAR: 2,
            Mode.BICYCLE: 1,
            Mode.PEDESTRIAN: 1,
        }
        assert live.stats.peak_active == 4

    def test_counts_arrivals_when_ids_disappear(self, traci_mock) -> None:
        _clock(traci_mock)
        live = LiveEngine(FakeSource(), [])
        traci_mock.vehicle.getIDList.return_value = ("car_0", "bike_0")
        traci_mock.person.getIDList.return_value = ("ped_0", "ped_1")
        live.step()

        traci_mock.vehicle.getIDList.return_value = ("bike_0",)
        traci_mock.person.getIDList.return_value = ("ped_1",)
        live.step()

        assert live.stats.arrived == {
            Mode.CAR: 1,
            Mode.BICYCLE: 0,
            Mode.PEDESTRIAN: 1,
        }
        assert live.stats.peak_active == 4  # the peak is kept after the count drops

    def test_logs_progress_every_fifteen_simulated_minutes(
        self, traci_mock, caplog
    ) -> None:
        _clock(traci_mock, start=START_TIME + engine.LOG_INTERVAL_SECONDS - 1)
        live = LiveEngine(FakeSource(), [])

        with caplog.at_level(logging.INFO, logger="simulator.engine"):
            live.step()  # reaches 05:15:00
            live.step()  # no second line for the same quarter hour

        lines = [r.message for r in caplog.records if "active:" in r.message]
        assert len(lines) == 1
        assert lines[0].startswith("05:15:00")


class TestRun:
    def test_stops_at_max_sim_seconds_and_closes(self, traci_mock) -> None:
        _clock(traci_mock)
        live = LiveEngine(FakeSource(), ["sumo"], max_sim_seconds=5)

        stats = live.run()

        assert traci_mock.simulationStep.call_count == 5
        traci_mock.close.assert_called_once()
        assert isinstance(stats, EngineStats)

    def test_without_a_bound_it_runs_until_interrupted(self, traci_mock) -> None:
        _clock(traci_mock)
        original = traci_mock.simulationStep.side_effect
        calls = {"n": 0}

        def step() -> None:
            calls["n"] += 1
            if calls["n"] > 50:
                raise KeyboardInterrupt
            original()

        traci_mock.simulationStep.side_effect = step

        LiveEngine(FakeSource(), ["sumo"]).run()

        assert calls["n"] == 51
        traci_mock.close.assert_called_once()

    def test_ends_quietly_when_sumo_closes(self, traci_mock) -> None:
        traci_mock.simulationStep.side_effect = FatalTraCIError("closed")
        traci_mock.close.side_effect = FatalTraCIError("already gone")

        stats = LiveEngine(FakeSource(), ["sumo-gui"]).run()  # must not raise

        assert isinstance(stats, EngineStats)
        traci_mock.close.assert_called_once()

    def test_closes_even_when_something_unexpected_fails(self, traci_mock) -> None:
        traci_mock.simulationStep.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            LiveEngine(FakeSource(), ["sumo"]).run()

        traci_mock.close.assert_called_once()


class TestBuildSumoArgs:
    def test_headless_starts_empty_at_five(self) -> None:
        args = _build_sumo_args(
            Path("net.net.xml"), headless=True, gui_settings_file=None, delay_ms=200
        )

        assert args[0] == "sumo"
        assert args[args.index("--begin") + 1] == "18000"
        assert args[args.index("-n") + 1] == "net.net.xml"
        assert "--delay" not in args
        assert "--route-files" not in args

    def test_gui_starts_on_its_own_with_delay_and_settings(self) -> None:
        args = _build_sumo_args(
            Path("net.net.xml"),
            headless=False,
            gui_settings_file=Path("view.xml"),
            delay_ms=150,
        )

        assert args[0] == "sumo-gui"
        assert "--start" in args
        assert args[args.index("--delay") + 1] == "150"
        assert args[args.index("--gui-settings-file") + 1] == "view.xml"

    def test_gui_without_settings_omits_the_flag(self) -> None:
        args = _build_sumo_args(
            Path("n.xml"), headless=False, gui_settings_file=None, delay_ms=200
        )

        assert "--gui-settings-file" not in args


class TestRunLive:
    def test_wires_source_and_engine_together(self, tmp_path: Path) -> None:
        with (
            patch("simulator.engine.load_demand_profile") as mock_profile,
            patch("simulator.engine.describe", return_value="a summary"),
            patch("simulator.engine.load_mode_edges") as mock_edges,
            patch("simulator.engine.RandomIndividualSource") as mock_source,
            patch("simulator.engine.LiveEngine") as mock_engine,
        ):
            result = run_live(
                tmp_path / "n.net.xml",
                headless=True,
                seed=9,
                max_sim_seconds=60,
                demand_file=tmp_path / "demand.json",
            )

        mock_profile.assert_called_once_with(tmp_path / "demand.json")
        mock_edges.assert_called_once_with(tmp_path / "n.net.xml")
        mock_source.assert_called_once_with(
            mock_edges.return_value,
            mock_profile.return_value,
            start_time=START_TIME,
            seed=9,
        )
        args, kwargs = mock_engine.call_args
        assert args[0] is mock_source.return_value
        assert args[1][0] == "sumo"
        assert kwargs == {"max_sim_seconds": 60}
        assert result is mock_engine.return_value.run.return_value

    def test_logs_what_demand_is_used(self, tmp_path: Path, caplog) -> None:
        with (
            patch("simulator.engine.load_demand_profile"),
            patch("simulator.engine.describe", return_value="15,000 trips/day"),
            patch("simulator.engine.load_mode_edges"),
            patch("simulator.engine.RandomIndividualSource"),
            patch("simulator.engine.LiveEngine"),
            caplog.at_level(logging.INFO, logger="simulator.engine"),
        ):
            run_live(tmp_path / "n.net.xml", headless=True)

        assert "Demand: 15,000 trips/day" in caplog.text

    def test_uses_the_committed_statistics_by_default(self, tmp_path: Path) -> None:
        with (
            patch("simulator.engine.load_demand_profile") as mock_profile,
            patch("simulator.engine.describe", return_value=""),
            patch("simulator.engine.load_mode_edges"),
            patch("simulator.engine.RandomIndividualSource"),
            patch("simulator.engine.LiveEngine"),
        ):
            run_live(tmp_path / "n.net.xml", headless=True)

        mock_profile.assert_called_once_with(DEFAULT_DEMAND_JSON)


def test_traci_mock_fixture_is_isolated() -> None:
    # Guard: the real traci module is untouched outside the fixture.
    assert not isinstance(engine.traci, MagicMock)
