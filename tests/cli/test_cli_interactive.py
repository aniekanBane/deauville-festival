from collections.abc import Iterator
from pathlib import Path

import pytest

from deauville_festival import cli_interactive, storage
from deauville_festival.festival import FestivalManager


@pytest.fixture
def interactive_manager(test_data_path: Path) -> FestivalManager:
    """Returns a FestivalManager backed by the isolated SQLite database."""
    store = storage.SQLiteStorage(test_data_path)
    return FestivalManager.from_storage(store)


def mock_pick(
    monkeypatch: pytest.MonkeyPatch, sequence: Iterator[tuple[str, int]]
) -> None:
    def fake_pick(
        _options: object = None,
        _title: object = None,
        _indicator: object = None,
        *args: object,
        **kwargs: object,
    ) -> tuple[str, int]:
        return next(sequence)

    monkeypatch.setattr(cli_interactive, "pick", fake_pick)


def mock_input(
    monkeypatch: pytest.MonkeyPatch,
    sequence: Iterator[str] | None = None,
    default_value: str = "",
) -> None:
    def fake_input(_prompt: object = "") -> str:
        if sequence is not None:
            return next(sequence)
        return default_value

    monkeypatch.setattr("builtins.input", fake_input)


class TestCliInteractiveCriticalPaths:
    """Tests critical navigation and operational paths in cli_interactive."""

    def test_run_main_menu_festival_info_and_exit(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(monkeypatch, iter([("Festival info", 0), ("Exit", 6)]))
        mock_input(monkeypatch)

        cli_interactive.run(interactive_manager)

        out = capsys.readouterr().out
        assert "Deauville Festival du Rire 2027" in out
        assert "Goodbye!" in out

    def test_run_main_menu_venues_and_exit(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(monkeypatch, iter([("Venues", 1), ("Exit", 6)]))
        mock_input(monkeypatch)

        cli_interactive.run(interactive_manager)

        out = capsys.readouterr().out
        assert "Grand Casino" in out
        assert "Goodbye!" in out

    def test_pick_artists_view_details_and_back(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(monkeypatch, iter([("Artist 1", 0), ("< Back", 13)]))
        mock_input(monkeypatch)

        cli_interactive.pick_artists(interactive_manager)

        out = capsys.readouterr().out
        assert "About" in out
        assert "Élodie Marchal" in out

    def test_pick_programme_filter_and_back(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(
            monkeypatch,
            iter([("Thursday", 1), ("Grand Casino", 1), ("< Back", 5)]),
        )
        mock_input(monkeypatch)

        cli_interactive.pick_programme(interactive_manager)

        out = capsys.readouterr().out
        assert "Opening Gala" in out

    def test_pick_on_now_current_time(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(monkeypatch, iter([("Current time", 0), ("< Back", 2)]))
        mock_input(monkeypatch)

        cli_interactive.pick_on_now(interactive_manager)

        out = capsys.readouterr().out
        assert "On stage at" in out

    def test_pick_on_now_custom_datetime(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(
            monkeypatch,
            iter([("Enter custom date and time", 1), ("< Back", 2)]),
        )
        mock_input(monkeypatch, iter(["2027-06-10T21:00", ""]))

        cli_interactive.pick_on_now(interactive_manager)

        out = capsys.readouterr().out
        assert "On stage at 2027-06-10 21:00" in out

    def test_pick_browse_performances_and_back(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(monkeypatch, iter([("Show 1", 0), ("< Back", 23)]))
        mock_input(monkeypatch)

        cli_interactive.pick_browse_performances(interactive_manager)

        out = capsys.readouterr().out
        assert "Opening Gala (Lineup)" in out
        assert "ID:" in out

    def test_pick_cancel_performance_confirmed(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(monkeypatch, iter([("Opening Gala", 0)]))
        mock_input(monkeypatch, default_value="y")

        target_id = "grand-casino-2027-06-10-2030"
        assert interactive_manager.performance_exists(target_id)

        cli_interactive.pick_cancel_performance(interactive_manager)

        assert not interactive_manager.performance_exists(target_id)
        out = capsys.readouterr().out
        assert "Cancelled: Opening Gala" in out

    def test_pick_cancel_performance_aborted(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(monkeypatch, iter([("Opening Gala", 0)]))
        mock_input(monkeypatch, default_value="n")

        target_id = "grand-casino-2027-06-10-2030"
        cli_interactive.pick_cancel_performance(interactive_manager)

        assert interactive_manager.performance_exists(target_id)
        out = capsys.readouterr().out
        assert "Cancellation aborted." in out

    def test_pick_performances_menu_browse_and_back(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_pick(
            monkeypatch,
            iter([("Browse performances", 0), ("< Back", 23), ("< Back", 3)]),
        )
        mock_input(monkeypatch)

        cli_interactive.pick_performances(interactive_manager)

    def test_pick_add_performance_solo(
        self,
        interactive_manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mock_pick(
            monkeypatch,
            iter([("Solo", 0), ("La Cabane", 3), ("Élodie Marchal", 0)]),
        )
        inputs = iter(
            [
                "New Solo Show",  # title
                "2027-06-10T14:00",  # start
                "60",  # duration
                "12",  # min age
                "",  # description
            ]
        )
        mock_input(monkeypatch, inputs)

        cli_interactive.pick_add_performance(interactive_manager)

        out = capsys.readouterr().out
        assert "Added: la-cabane-2027-06-10-1400" in out
        assert interactive_manager.performance_exists("la-cabane-2027-06-10-1400")
