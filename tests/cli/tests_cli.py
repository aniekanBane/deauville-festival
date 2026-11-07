from datetime import date
from pathlib import Path

import pytest

from deauville_festival import cli, config, storage
from deauville_festival.festival import FestivalManager
from deauville_festival.models import Artist, SoloPerformance, Venue

_SOURCE_DATA_PATH = config.DATA_DIR / "festival.json"


@pytest.fixture
def cli_data_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Creates an isolated SQLite database and patches the CLI data directory."""
    database_path = tmp_path / "festival.db"
    storage.SQLiteStorage(database_path).save(
        storage.JSONFileStorage(_SOURCE_DATA_PATH).load()
    )
    monkeypatch.setattr(cli.config, "DATA_DIR", tmp_path)
    return database_path


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
        assert lines[1] == "-----------"
        # First artist by slug is elodie-marchal ("Élodie Marchal")
        assert lines[2].startswith("Élodie Marchal (elodie-marchal)")
        assert lines[2].endswith("| 3 shows")

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
        assert (
            capsys.readouterr().out.strip()
            == "Artists: 0\n----------\nNo artists found."
        )

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
            ["deauville-festival", "artists", "--focus", "paul-kerbrat"],
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

        cli.cli_prompts.display_artist_info(manager, "newcomer")

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
            ["deauville-festival", "artists", "--focus", "unknown-artist"],
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
            "sys.argv", ["deauville-festival", "programme", "--day", "2027-06-10"]
        )

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Programme: Thursday 10 June | All venues" in out
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

        cli.cli_prompts.display_programme(empty_manager, day=date(2027, 6, 10))

        assert "No performances found for this selection." in capsys.readouterr().out

    @pytest.mark.parametrize("bad_day", ["not-a-date"])
    def test_programme_command_with_out_of_range_or_invalid_date_returns_1(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        bad_day: str,
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["deauville-festival", "programme", "--day", bad_day]
        )

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
        assert "On stage at 2027-06-10 21:15" in out
        assert "- Opening Gala at Grand Casino, until 22:30" in out
        assert "- Family Business at Théâtre des Planches, until 22:15" in out
        assert "Up next" in out
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
        assert "No performances happening at the moment." in out
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
        assert "Added artist: Claire Dumont (claire-dumont)." in out
        saved_slugs = {
            a.slug for a in storage.SQLiteStorage(cli_data_path).load()["artists"]
        }
        assert "claire-dumont" in saved_slugs

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
                "la-cabane",
                "2027-06-10T14:00",
                "",
                "60",
                "sacha-diallo",
                "0",
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert (
            "Added: la-cabane-2027-06-10-1400, the 1st event of the programme 2027-06-10."
            in out
        )
        saved_ids = {
            p.id for p in storage.SQLiteStorage(cli_data_path).load()["performances"]
        }
        assert "la-cabane-2027-06-10-1400" in saved_ids

    def test_add_command_adds_lineup_performance(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["deauville-festival", "add", "--kind", "lineup"]
        )
        inputs = iter(
            [
                "Comedy Showcase",
                "la-cabane",
                "2027-06-11T14:00",
                "A fun lineup show",
                "90",
                "paul-kerbrat",
                "hugo-lemaire, ines-moreau",
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Added: la-cabane-2027-06-11-1400" in out
        saved_ids = {
            p.id for p in storage.SQLiteStorage(cli_data_path).load()["performances"]
        }
        assert "la-cabane-2027-06-11-1400" in saved_ids

    def test_add_command_adds_workshop_performance(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.setattr(
            "sys.argv", ["deauville-festival", "add", "--kind", "workshop"]
        )
        inputs = iter(
            [
                "Improv Masterclass",
                "le-kiosque",
                "2027-06-12T10:00",
                "Learn the basics of improv",
                "60",
                "ines-moreau",
                "15",
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        exit_code = cli.main()

        assert exit_code == 0
        out = capsys.readouterr().out
        assert "Added: le-kiosque-2027-06-12-1000" in out
        saved_ids = {
            p.id for p in storage.SQLiteStorage(cli_data_path).load()["performances"]
        }
        assert "le-kiosque-2027-06-12-1000" in saved_ids

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
                "la-cabane",
                "2027-06-10T21:00",
                "",
                "60",
                "sacha-diallo",
                "0",
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


class TestDisplayPerformanceDetailsCli:
    """Tests for `cli.display_performance_details`."""

    def test_display_performance_details_success(
        self, manager: FestivalManager, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cli.display_performance_details(manager, "grand-casino-2027-06-10-2030")
        out = capsys.readouterr().out
        assert "Opening Gala (Lineup)" in out
        assert "Grand Casino" in out

    def test_display_performance_details_not_found(
        self, manager: FestivalManager
    ) -> None:
        with pytest.raises(cli.errors.NotFoundError):
            cli.display_performance_details(manager, "unknown-id")


class TestCliPromptsHelpers:
    """Tests for cli_prompts helper and parser functions."""

    def test_parse_duration_invalid(self) -> None:
        with pytest.raises(ValueError, match="not a valid number of minutes"):
            cli.cli_prompts.parse_duration("abc")

    def test_parse_min_age_invalid(self) -> None:
        with pytest.raises(ValueError, match="not a valid number of years"):
            cli.cli_prompts.parse_min_age("abc")

    def test_parse_max_participants_invalid(self) -> None:
        with pytest.raises(ValueError, match="not a valid number of participants"):
            cli.cli_prompts.parse_max_participants("abc")

    def test_display_performance_details_prompts_all_kinds(
        self, manager: FestivalManager, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Solo
        solo = manager.get_performance_by_id("theatre-des-planches-2027-06-10-2100")
        assert solo is not None
        details_solo = manager.get_performance_details(solo)
        details_solo["min_age"] = 16
        cli.cli_prompts.display_performance_details(details_solo)
        out = capsys.readouterr().out
        assert "Sacha Diallo" in out
        assert "Min Age:      16+" in out

        # Lineup
        lineup = manager.get_performance_by_id("grand-casino-2027-06-10-2030")
        assert lineup is not None
        cli.cli_prompts.display_performance_details(
            manager.get_performance_details(lineup)
        )
        out = capsys.readouterr().out
        assert "Paul Kerbrat" in out

        # Workshop
        workshop = manager.get_performance_by_id("la-cabane-2027-06-11-1030")
        assert workshop is not None
        cli.cli_prompts.display_performance_details(
            manager.get_performance_details(workshop)
        )
        out = capsys.readouterr().out
        assert "Places left:" in out
        assert "Participants:" in out

    def test_display_performances_now_default_moment(
        self,
        manager: FestivalManager,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        from datetime import datetime

        class FakeDatetime(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2027, 6, 10, 21, 0)

        monkeypatch.setattr(cli.cli_prompts, "datetime", FakeDatetime)
        cli.cli_prompts.display_performances_now(manager, None)
        out = capsys.readouterr().out
        assert "On stage at 2027-06-10 21:00" in out


class TestCliOtherCommands:
    """Tests for interactive, serve, and add edge cases."""

    def test_add_unknown_kind_raises_value_error(
        self, manager: FestivalManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        inputs = iter(["Title", "la-cabane", "2027-06-10T14:00", "Desc", "60"])
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
        with pytest.raises(ValueError, match="Unknown performance kind 'magic'"):
            cli.add_performance(manager, kind="magic")

    def test_add_ordinal_3rd_and_th(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        # On day 2027-06-10:
        # Currently 3 performances exist (20:30, 21:00, 22:30). Adding at 21:30 gives 3rd:
        inputs_3rd = iter(
            [
                "Third Show",
                "la-cabane",
                "2027-06-10T21:30",
                "",
                "45",
                "ines-moreau",
                "0",
            ]
        )
        monkeypatch.setattr("sys.argv", ["deauville-festival", "add"])
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs_3rd))
        exit_code = cli.main()
        assert exit_code == 0
        assert "the 3rd event of the programme 2027-06-10" in capsys.readouterr().out

        # Adding at 23:00 gives 5th (after Third Show was added), testing 'th' suffix:
        inputs_4th = iter(
            [
                "Fourth Show",
                "la-cabane",
                "2027-06-10T23:00",
                "",
                "45",
                "jeanne-aubry",
                "0",
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs_4th))
        exit_code = cli.main()
        assert exit_code == 0
        assert "the 5th event of the programme 2027-06-10" in capsys.readouterr().out

    def test_interactive_command(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import deauville_festival.cli_interactive

        called: list[bool] = []

        def fake_run(_manager: object) -> None:
            called.append(True)

        monkeypatch.setattr(deauville_festival.cli_interactive, "run", fake_run)
        monkeypatch.setattr("sys.argv", ["deauville-festival", "interactive"])
        exit_code = cli.main()
        assert exit_code == 0
        assert called == [True]

    def test_serve_command(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        import uvicorn

        called: list[tuple[object, object]] = []

        def fake_uvicorn_run(app: object, host: str = "0.0.0.0") -> None:  # noqa: S104
            called.append((app, host))

        monkeypatch.setattr(uvicorn, "run", fake_uvicorn_run)
        monkeypatch.setattr("sys.argv", ["deauville-festival", "serve"])
        exit_code = cli.main()
        assert exit_code == 0
        assert len(called) == 1

    def test_default_help_subcommand(
        self,
        cli_data_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        def fake_parse_args(
            _self: cli.argparse.ArgumentParser,
        ) -> cli.argparse.Namespace:
            return cli.argparse.Namespace(command="unknown")

        monkeypatch.setattr(
            cli.argparse.ArgumentParser,
            "parse_args",
            fake_parse_args,
        )
        exit_code = cli.main()
        assert exit_code == 0
        out = capsys.readouterr().out
        assert "usage:" in out
