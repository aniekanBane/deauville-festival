import shutil
from datetime import date
from pathlib import Path

import pytest

from deauville_festival import cli, errors, storage
from deauville_festival.festival import FestivalManager
from deauville_festival.models import Artist, SoloPerformance, Venue

_SOURCE_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "festival.json"


@pytest.fixture
def cli_data_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copies the festival JSON to a temporary directory and patches `cli._FILE_PATH`."""
    temp_file = tmp_path / "festival.json"
    shutil.copy(_SOURCE_DATA_PATH, temp_file)
    monkeypatch.setattr(cli, "_FILE_PATH", temp_file)
    return temp_file


@pytest.fixture
def manager(cli_data_path: Path) -> FestivalManager:
    """Returns a `FestivalManager` loaded from the temporary data file."""
    data = storage.load_data(cli_data_path)
    return FestivalManager(**data)


class TestDisplayFestivalInfo:
    """Tests for `cli.display_festival_info` and `cli.main` with no subcommand."""

    def test_main_without_arguments_displays_festival_info(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["deauville-festival"])

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Deauville Festival du Rire 2027" in out
        assert "From 2027-06-10 to 2027-06-13" in out
        assert "4 venues, 12 artists, 23 performances" in out


class TestDisplayVenues:
    """Tests for `cli.display_venues` and the `venues` subcommand."""

    def test_venues_command_lists_venues_and_total_seats(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["deauville-festival", "venues"])

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Venues: 4" in out
        assert "grand-casino: Grand Casino (Seafront, main hall), 650 seats" in out
        assert (
            "la-cabane: La Cabane (Beach, next to the lifeguard post), 40 seats" in out
        )
        assert "Total: 1130 seats" in out


class TestDisplayArtists:
    """Tests for `cli.display_artists`, `cli.display_artist_info`, and `artists` subcommand."""

    def test_artists_command_lists_artists_alphabetically_with_show_counts(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["deauville-festival", "artists"])

        exit_code = cli.main()

        assert exit_code == 0
        lines = capsys.readouterr().out.strip().splitlines()
        assert lines[0] == "Artists: 12"
        # First artist by slug is elodie-marchal ("Élodie Marchal")
        assert lines[1].startswith("Élodie Marchal (elodie-marchal)")
        assert lines[1].endswith("| 3 shows")

    def test_display_artists_handles_empty_and_singular_show(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        empty_manager = FestivalManager(
            name="Test Festival",
            first_day=date(2027, 6, 10),
            last_day=date(2027, 6, 13),
            venues=[Venue(name="Le Kiosque", capacity=100, address="Beach")],
            artists=[],
            performances=[],
        )
        cli.display_artists(empty_manager)
        assert capsys.readouterr().out.strip() == "Artists: 0"

        artist = Artist(name="Solo Star", bio="Bio", photo_url="")
        empty_manager.add_artist(artist)
        empty_manager.add_performance(
            SoloPerformance(
                title="One Show Only",
                venue="le-kiosque",
                start=cli.helpers.datetime_from_str("2027-06-10T20:00"),
                duration_minutes=60,
                artist="solo-star",
            )
        )
        cli.display_artists(empty_manager)
        out = capsys.readouterr().out
        assert "Solo Star (solo-star) | 1 show\n" in out

    def test_artist_info_command_displays_bio_and_performances_with_roles(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["deauville-festival", "artists", "--find", "paul-kerbrat"],
        )

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Paul Kerbrat (paul-kerbrat)" in out
        assert "Breton host, master of ceremonies of the festival." in out
        assert "Opening Gala (host)" in out
        assert "Stand-up Lab (teacher)" in out

    def test_display_artist_info_with_no_performances(
        self,
        manager: FestivalManager,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        manager.add_artist(Artist(name="Newcomer", bio="Just arrived.", photo_url=""))

        cli.display_artist_info("newcomer", manager)

        out = capsys.readouterr().out
        assert "Newcomer (newcomer)" in out
        assert "No performances found for this artist." in out

    def test_artist_info_unknown_slug_returns_error_code_1(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["deauville-festival", "artists", "--find", "unknown-artist"],
        )

        exit_code = cli.main()

        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Error: Artist 'unknown-artist' not found." in err


class TestDisplayProgramme:
    """Tests for `cli.display_programme` and the `programme` subcommand."""

    def test_programme_command_displays_day_schedule_in_order(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["deauville-festival", "programme", "2027-06-10"]
        )

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Programme for Thursday 10 June:" in out
        assert "20:30-22:30" in out
        assert "Opening Gala (lineup)" in out
        assert "Family Business (solo)" in out
        assert "Open Mic Night (lineup)" in out

    def test_display_programme_when_day_has_no_performances(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        empty_manager = FestivalManager(
            name="Test Festival",
            first_day=date(2027, 6, 10),
            last_day=date(2027, 6, 13),
            venues=[Venue(name="Le Kiosque", capacity=100, address="Beach")],
            artists=[],
            performances=[],
        )

        cli.display_programme("2027-06-10", empty_manager)

        assert (
            capsys.readouterr().out.strip() == "No performances found for 2027-06-10."
        )

    @pytest.mark.parametrize("bad_day", ["2027-06-09", "2027-06-15", "not-a-date"])
    def test_programme_command_with_out_of_range_or_invalid_date_returns_1(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        bad_day: str,
    ) -> None:
        monkeypatch.setattr("sys.argv", ["deauville-festival", "programme", bad_day])

        exit_code = cli.main()

        assert exit_code == 1
        assert "Error:" in capsys.readouterr().err


class TestDisplayPerformancesNow:
    """Tests for `cli.display_performances_now` and the `now` subcommand."""

    def test_now_command_with_ongoing_and_upcoming_performances(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["deauville-festival", "now", "2027-06-10T21:15"]
        )

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "On stage at 2027-06-10 21:15:" in out
        assert "- Opening Gala at Grand Casino, until 22:30" in out
        assert "- Family Business at Théâtre des Planches, until 22:15" in out
        assert "Up next:" in out
        assert "Open Mic Night (lineup)" in out

    def test_now_command_when_nothing_on_stage_and_after_festival(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["deauville-festival", "now", "2027-06-13T23:59"]
        )

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "No performances happening at 2027-06-13 23:59." in out
        assert "No upcoming performances." in out

    def test_now_command_with_invalid_datetime_returns_1(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["deauville-festival", "now", "invalid-moment"])

        exit_code = cli.main()

        assert exit_code == 1
        assert "Error:" in capsys.readouterr().err


class TestAddArtistAndPerformanceCli:
    """Tests for `cli.add_artist`, `cli.parse_duration`, and `cli.add_performance`."""

    def test_add_artist_interactive_persists_and_prints_confirmation(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["deauville-festival", "artists", "--add"])
        inputs = iter(
            ["Claire Dumont", "Stand-up comedian.", "https://example.com/c.jpg"]
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Added: artist Claire Dumont (claire-dumont)." in out
        saved_slugs = {
            a.slug for a in storage.JSONFileStorage(cli_data_path).load()["artists"]
        }
        assert "claire-dumont" in saved_slugs

    def test_parse_duration_valid_and_invalid(self) -> None:
        assert cli.parse_duration("  90 ") == 90

        with pytest.raises(errors.InvalidError):
            cli.parse_duration("   ")

        with pytest.raises(ValueError, match="not a valid number of minutes"):
            cli.parse_duration("sixty")

    def test_add_command_adds_solo_performance_and_prints_event_number(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["deauville-festival", "add"])
        inputs = iter(
            [
                "Afternoon Warmup",
                "sacha-diallo",
                "la-cabane",
                "2027-06-10T14:00",
                "60",
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert (
            "Added: la-cabane-2027-06-10-1400, Event 1 of the programme 2027-06-10."
            in out
        )
        saved_ids = {
            p.id for p in storage.JSONFileStorage(cli_data_path).load()["performances"]
        }
        assert "la-cabane-2027-06-10-1400" in saved_ids

    def test_add_command_with_conflict_returns_1(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr("sys.argv", ["deauville-festival", "add"])
        # Sacha Diallo is already on stage at theatre-des-planches on 2027-06-10T21:00
        inputs = iter(
            [
                "Clashing Show",
                "sacha-diallo",
                "la-cabane",
                "2027-06-10T21:00",
                "60",
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        exit_code = cli.main()

        assert exit_code == 1
        assert "Error: Sacha Diallo is busy" in capsys.readouterr().err


class TestCancelPerformanceCli:
    """Tests for `cli.cancel_performance` and the `cancel` subcommand."""

    def test_cancel_command_removes_performance_and_persists(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        target_id = "grand-casino-2027-06-10-2030"
        monkeypatch.setattr("sys.argv", ["deauville-festival", "cancel", target_id])

        exit_code = cli.main()

        assert exit_code == 0
        assert "Cancelled: Opening Gala" in capsys.readouterr().out
        saved_ids = {p.id for p in storage.load_data(cli_data_path)["performances"]}
        assert target_id not in saved_ids

    def test_cancel_command_with_unknown_id_returns_1(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["deauville-festival", "cancel", "nonexistent-id"]
        )

        exit_code = cli.main()

        assert exit_code == 1
        assert (
            "Error: Performance 'nonexistent-id' not found." in capsys.readouterr().err
        )
