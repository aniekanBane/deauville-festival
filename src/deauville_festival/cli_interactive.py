import sys
import typing
from collections.abc import Sequence

from pick import pick

from deauville_festival import cli_prompts, config, errors, helpers
from deauville_festival.festival import FestivalManager
from deauville_festival.models import (
    LineupPerformance,
    Performance,
    SoloPerformance,
    WorkshopPerformance,
)

INDICATOR = "*> "
CANCEL_OPT = "< Cancel"
GO_BACK_OPT = "< Back to Main Menu"
MAIN_MENU_PROMPT = "\nPress Enter to return to the main menu..."
ENTER_PROMPT = "\nPress Enter to continue..."


def _pick_browse_artists(manager: FestivalManager) -> None:
    """Lists artists and allows selecting one to view details."""
    artists = manager.list_artists()
    if not artists:
        print("\nNo artists found.")
        input("Press Enter to return to artists menu...")
        return

    options = cli_prompts.format_artists_lines(manager)
    options.append("< Back to Artists Menu")

    title = f"Artists ({len(artists)}) | Select to view details:"
    _, index = pick(options, title=title, indicator=INDICATOR)

    index = typing.cast(int, index)
    if index == len(artists):
        return

    selected_artist = artists[index]
    cli_prompts.display_artist_info(manager, selected_artist.slug)
    input("\nPress Enter to return to artists menu...")


def _pick_add_artist(manager: FestivalManager) -> None:
    """Prompts to add a new artist."""
    try:
        print("\n--- Add Artist ---")
        cli_prompts.add_artist(manager)
    except (ValueError, errors.FestivalError) as err:
        print(f"Error: {err}", file=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        print("\nAdding cancelled.")
    input("\nPress Enter to return to artists menu...")


def pick_artists(manager: FestivalManager) -> None:
    """Submenu for artists: browse and add new artists."""
    options = [
        "Browse artists",
        "Add new artist",
        GO_BACK_OPT,
    ]

    while True:
        _, index = pick(options, title="Artists:", indicator=INDICATOR)
        if index == 0:
            _pick_browse_artists(manager)
        elif index == 1:
            _pick_add_artist(manager)
        else:
            return


def pick_programme(manager: FestivalManager) -> None:
    """Allows selecting a day and venue to view the programme."""
    days = manager.get_festival_days()
    venues = manager.list_venues()

    while True:
        # Step 1: Select Day
        day_options = (
            ["All days"] + [d.strftime("%A %d %B %Y") for d in days] + [GO_BACK_OPT]
        )
        _, day_index = pick(
            day_options,
            title="Programme - Select a day:",
            indicator=INDICATOR,
        )

        day_index = typing.cast(int, day_index)
        if day_index == len(day_options) - 1:
            return

        chosen_day = None if day_index == 0 else days[day_index - 1]

        # Step 2: Select Venue
        venue_options = (
            ["All venues"] + [f"{v.name}" for v in venues] + ["< Back to day selection"]
        )
        _, venue_index = pick(
            venue_options,
            title=f"Programme - Day: {day_options[day_index]} — Select a venue:",
            indicator=INDICATOR,
        )

        venue_index = typing.cast(int, venue_index)
        if venue_index == len(venue_options) - 1:
            continue

        chosen_venue_slug = None if venue_index == 0 else venues[venue_index - 1].slug

        # Display results
        cli_prompts.display_programme(
            manager, day=chosen_day, venue_slug=chosen_venue_slug
        )
        input("\nPress Enter to return to programme selection...")


def pick_on_now(manager: FestivalManager) -> None:
    """Lets the user check what is on now or at a specific datetime."""
    options = [
        "Current time",
        "Enter custom date and time",
        GO_BACK_OPT,
    ]
    title = "Select moment to check:"

    while True:
        _, index = pick(options, title=title, indicator=INDICATOR)

        if index == 0:
            cli_prompts.display_performances_now(manager)
            input(ENTER_PROMPT)
        elif index == 1:
            raw = input("\nEnter date and time (YYYY-MM-DDTHH:MM): ").strip()
            if not raw:
                continue
            try:
                moment = helpers.datetime_from_str(raw)
            except (errors.InvalidDateTimeFormatError, ValueError) as err:
                print(f"Error: {err}", file=sys.stderr)
                input(ENTER_PROMPT)
                continue
            cli_prompts.display_performances_now(manager, moment)
            input(ENTER_PROMPT)
        elif index == 2:
            return


def format_performance_options(
    manager: FestivalManager, performances: Sequence[Performance]
) -> list[str]:
    """Formats performances into pick-ready option lines aligned by venue name."""
    if not performances:
        return []

    venue_name_map = manager.get_venue_slug_to_name_map()
    venue_name_max_len = max(len(name) for name in venue_name_map.values())

    return [
        f"{p.start:%a %d %b %H:%M} | "
        f"{venue_name_map.get(p.venue, p.venue):<{venue_name_max_len}} | "
        f"{p.title} ({p.kind})"
        for p in performances
    ]


def pick_browse_performances(manager: FestivalManager) -> None:
    """Allows selecting a performance to view its full details."""
    while True:
        performances = manager.list_performances()
        if not performances:
            print("\nNo performances found.")
            input("Press Enter to continue...")
            return

        options = format_performance_options(manager, performances)
        options.append("< Back to Performances Menu")

        title = f"Performances ({len(performances)}) | Select to view details:"
        _, index = pick(options, title=title, indicator=INDICATOR)

        index = typing.cast(int, index)
        if index == len(performances):
            return

        selected_perf = performances[index]
        details = manager.get_performance_details(selected_perf)
        cli_prompts.display_performance_details(details)
        input("\nPress Enter to return to performances...")


def pick_add_performance(manager: FestivalManager) -> None:
    """Prompts for details and adds a performance (Solo, Lineup, or Workshop)."""
    kind_options = [
        "Solo Performance",
        "Lineup Performance",
        "Workshop",
        CANCEL_OPT,
    ]
    _, kind_index = pick(
        kind_options, title="Select performance type to add:", indicator=INDICATOR
    )

    if kind_index == len(kind_options) - 1:
        print("Adding cancelled.")
        return

    print("\n--- Add Performance ---")
    title_input = input("Title: ")
    title = Performance.validate_title(title_input)

    venues = manager.list_venues()
    if not venues:
        print("No venues available.")
        return

    venue_options = [f"{v.name} ({v.slug})" for v in venues] + [CANCEL_OPT]
    _, v_index = pick(venue_options, title="Select Venue:", indicator=INDICATOR)

    v_index = typing.cast(int, v_index)
    if v_index == len(venues):
        print("Adding cancelled.")
        return

    chosen_venue_slug = venues[v_index].slug

    start_input = input("Start (YYYY-MM-DDTHH:MM): ")
    start = helpers.datetime_from_str(start_input)

    duration_input = input("Duration (minutes): ")
    duration = Performance.validate_duration_minutes(
        cli_prompts.parse_duration(duration_input)
    )

    artists = manager.list_artists()
    if not artists:
        print("No artists available. Add an artist first.")
        return

    performance: Performance
    if kind_index == 0:
        # Solo Performance
        artist_options = [f"{a.name} ({a.slug})" for a in artists] + [CANCEL_OPT]
        _, a_index = pick(artist_options, title="Select Artist:", indicator=INDICATOR)

        a_index = typing.cast(int, a_index)
        if a_index == len(artists):
            print("Adding cancelled...")
            return
        chosen_artist_slug = artists[a_index].slug

        min_age_input = input("Minimum age (0-18, press Enter for 0): ").strip()
        min_age = cli_prompts.parse_min_age(min_age_input)

        performance = SoloPerformance(
            title=title,
            artist=chosen_artist_slug,
            venue=chosen_venue_slug,
            start=start,
            duration_minutes=duration,
            min_age=min_age,
        )

    elif kind_index == 1:
        # Lineup Performance
        host_options = [f"{a.name} ({a.slug})" for a in artists] + [CANCEL_OPT]
        _, h_index = pick(host_options, title="Select Host:", indicator=INDICATOR)

        h_index = typing.cast(int, h_index)
        if h_index == len(artists):
            print("Adding cancelled.")
            return
        chosen_host_slug = artists[h_index].slug

        candidate_artists = [a for a in artists if a.slug != chosen_host_slug]
        if len(candidate_artists) < LineupPerformance.ACTS_MIN_LEN:
            print(
                f"Not enough artists for a lineup (need at least {LineupPerformance.ACTS_MIN_LEN} acts besides the host)."
            )
            return

        act_options = [f"{a.name} ({a.slug})" for a in candidate_artists]
        selected_acts = pick(
            act_options,
            title=(
                f"Select acts (at least {LineupPerformance.ACTS_MIN_LEN}, "
                "press Space to select, Enter to confirm):"
            ),
            multiselect=True,
            min_selection_count=LineupPerformance.ACTS_MIN_LEN,
            indicator=INDICATOR,
        )

        chosen_act_slugs = [candidate_artists[idx].slug for _, idx in selected_acts]

        performance = LineupPerformance(
            title=title,
            host=chosen_host_slug,
            acts=chosen_act_slugs,
            venue=chosen_venue_slug,
            start=start,
            duration_minutes=duration,
        )

    else:
        # Workshop Performance
        teacher_options = [f"{a.name} ({a.slug})" for a in artists] + [CANCEL_OPT]
        _, t_index = pick(teacher_options, title="Select Teacher:", indicator=INDICATOR)

        t_index = typing.cast(int, t_index)
        if t_index == len(artists):
            print("Adding cancelled.")
            return
        chosen_teacher_slug = artists[t_index].slug

        max_participants_input = input("Maximum participants (>= 1): ").strip()
        max_participants = cli_prompts.parse_max_participants(max_participants_input)

        performance = WorkshopPerformance(
            title=title,
            teacher=chosen_teacher_slug,
            max_participants=max_participants,
            venue=chosen_venue_slug,
            start=start,
            duration_minutes=duration,
        )

    description_input = input("Description: ")
    performance.description = Performance.validate_description(description_input)

    manager.add_performance(performance)

    performance_festival_day = performance.get_festival_day()
    day_performances = manager.list_performances(day=performance_festival_day)
    line_number = day_performances.index(performance) + 1

    print(
        f"\nAdded: {performance.id}, Event {line_number} of the programme {performance_festival_day}."
    )


def pick_cancel_performance(manager: FestivalManager) -> None:
    """Allows picking a performance to cancel."""
    performances = manager.list_performances()
    if not performances:
        print("\nNo performances found to cancel.")
        return

    options = format_performance_options(manager, performances)
    options.append("< Back to Performances Menu")

    title = "Select a performance to cancel:"
    _, index = pick(options, title=title, indicator=INDICATOR)

    index = typing.cast(int, index)
    if index == len(performances):
        return

    selected_perf = performances[index]
    confirm = (
        input(
            f"\nAre you sure you want to cancel '{selected_perf.title}' "
            f"({selected_perf.id})? (y/N): "
        )
        .strip()
        .lower()
    )

    if confirm in ("y", "yes"):
        cli_prompts.cancel_performance(manager, selected_perf.id)
    else:
        print("Cancellation aborted.")


def pick_performances(manager: FestivalManager) -> None:
    """Submenu for performances: browse/view details, add, and cancel."""
    options = [
        "Browse performances",
        "Add new performance",
        "Cancel a performance",
        GO_BACK_OPT,
    ]
    title = "Performances:"

    while True:
        _, index = pick(options, title=title, indicator=INDICATOR)

        if index == 0:
            pick_browse_performances(manager)
        elif index == 1:
            try:
                pick_add_performance(manager)
            except (ValueError, errors.FestivalError) as err:
                print(f"\nError: {err}", file=sys.stderr)
            input(ENTER_PROMPT)
        elif index == 2:
            try:
                pick_cancel_performance(manager)
            except errors.FestivalError as err:
                print(f"\nError: {err}", file=sys.stderr)
            input(ENTER_PROMPT)
        elif index == 3:
            return


TITLE = "Deauville Festival du Rire 2027"
MENU_OPTS = [
    "Festival info",
    "Venues",
    "Artists",
    "Performances",
    "Programme",
    "On now",
    "Exit",
]


def run(festival_manager: FestivalManager) -> None:
    while True:
        opt, _ = pick(MENU_OPTS, title=TITLE, indicator=INDICATOR)
        if opt == "Exit":
            print("Goodbye!")
            return
        if opt == "Festival info":
            cli_prompts.display_festival_info(festival_manager)
            input(MAIN_MENU_PROMPT)
        if opt == "Venues":
            cli_prompts.display_venues(festival_manager)
            input(MAIN_MENU_PROMPT)
        if opt == "Artists":
            pick_artists(festival_manager)
        if opt == "Performances":
            pick_performances(festival_manager)
        if opt == "Programme":
            pick_programme(festival_manager)
        if opt == "On now":
            pick_on_now(festival_manager)


if __name__ == "__main__":
    from deauville_festival.storage import SQLiteStorage, seed_database

    try:
        storage_backend = SQLiteStorage(config.DATA_DIR / "festival.db")
        seed_database(storage_backend)

        festival_manager = FestivalManager.from_storage(storage_backend)

        run(festival_manager)
    except errors.FestivalError as err:
        print(f"Error: {err}")
