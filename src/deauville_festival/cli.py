import argparse
import sys
from typing import Any

from deauville_festival import cli_prompts, config, errors, helpers
from deauville_festival.festival import FestivalManager
from deauville_festival.models import (
    PERFORMANCE_REGISTRY,
    LineupPerformance,
    Performance,
    SoloPerformance,
    WorkshopPerformance,
)
from deauville_festival.storage import SQLiteStorage, seed_database


def display_artists(manager: FestivalManager) -> None:
    """Lists all artists."""
    artists = manager.list_artists()

    title = f"Artists: {len(artists)}"
    print(f"\n{title}\n{'-' * len(title)}")
    if not artists:
        print("No artists found.")
        return

    labels = [str(artist) for artist in artists]
    max_label_len = max(len(label) for label in labels)

    for artist, label in zip(artists, labels, strict=True):
        count = len(manager.list_performances(artist_slug=artist.slug))
        s = "show" if count == 1 else "shows"
        print(f"{label:<{max_label_len}} | {count} {s}")


def display_performance_details(manager: FestivalManager, performance_id: str) -> None:
    """Displays the details of a specific performance."""
    performance = manager.get_performance_by_id(performance_id)
    if performance is None:
        raise errors.NotFoundError(f"Performance {performance_id} not found.")

    performance_details = manager.get_performance_details(performance)
    cli_prompts.display_performance_details(performance_details)


def add_performance(manager: FestivalManager, kind: str = "solo") -> None:
    """Prompts for details and adds a performance to the festival."""
    title = Performance.validate_title(input("Title: "))
    venue_slug = Performance.validate_venue(input("Venue (slug): "))
    start = helpers.datetime_from_str(input("Start (YYYY-MM-DDTHH:MM): "))
    description = Performance.validate_description(input("Description: "))
    duration = Performance.validate_duration_minutes(
        cli_prompts.parse_duration(input("Duration (1-360 minutes): "))
    )

    kwargs: dict[str, Any] = {
        "title": title,
        "venue": venue_slug,
        "start": start,
        "duration_minutes": duration,
        "description": description,
    }

    if kind == "solo":
        kwargs["artist"] = SoloPerformance.validate_artist(input("Artist (slug): "))
        kwargs["min_age"] = SoloPerformance.validate_min_age(
            cli_prompts.parse_min_age(input("Minimum age (0-18 years): "))
        )
    elif kind == "lineup":
        kwargs["host"] = LineupPerformance.validate_host(input("Host (slug): "))
        acts_input = input("Acts (comma-separated slugs): ")
        kwargs["acts"] = [a.strip() for a in acts_input.split(",") if a.strip()]
    elif kind == "workshop":
        kwargs["teacher"] = WorkshopPerformance.validate_teacher(
            input("Teacher (slug): ")
        )
        kwargs["max_participants"] = WorkshopPerformance.validate_max_participants(
            cli_prompts.parse_max_participants(input("Max participants (>= 1): "))
        )
    else:
        raise ValueError(
            f"Unknown performance kind '{kind}'. Must be 'solo', 'lineup', or 'workshop'."
        )

    performance = PERFORMANCE_REGISTRY[kind](**kwargs)

    manager.add_performance(performance)

    performance_festival_day = performance.get_festival_day()
    day_performances = manager.list_performances(day=performance_festival_day)
    line_number = day_performances.index(performance) + 1

    def _get_ordinal(n: int) -> str:
        n_str = str(n)
        if n_str.endswith("1"):
            return n_str + "st"
        elif n_str.endswith("2"):
            return n_str + "nd"
        elif n_str.endswith("3"):
            return n_str + "rd"
        else:
            return n_str + "th"

    print(
        f"Added: {performance.id}, the {_get_ordinal(line_number)} "
        f"event of the programme {performance_festival_day}."
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Display information about the Deauville Festival."
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("venues", help="Display information about the venues.")

    programme_parser = subparsers.add_parser(
        "programme", help="Display the programme for a specific day."
    )
    programme_parser.add_argument(
        "--day",
        help="The festival day (YYYY-MM-DD).",
    )
    programme_parser.add_argument(
        "--venue",
        help="The slug of the venue.",
    )

    artists_parser = subparsers.add_parser(
        "artists", help="Display information about the artists."
    )
    artists_parser.add_argument("--add", action="store_true", help="Add a new artist.")
    artists_parser.add_argument("--focus", help="The slug of the artist.")

    now_parser = subparsers.add_parser(
        "now", help="Display the performances happening now."
    )
    now_parser.add_argument(
        "moment",
        help="The date and time (YYYY-MM-DDTHH:MM).",
    )

    add_parser = subparsers.add_parser("add", help="Add a new performance.")
    add_parser.add_argument(
        "--kind",
        "-k",
        choices=["solo", "lineup", "workshop"],
        default="solo",
        help="The kind of performance to add (default: solo).",
    )

    cancel_parser = subparsers.add_parser("cancel", help="Cancel a performance.")
    cancel_parser.add_argument(
        "id",
        help="The ID of the performance (venue_slug-start(YYYY-MM-DD-HHMM)).",
    )

    subparsers.add_parser("interactive", help="Interactive mode.")

    subparsers.add_parser("serve", help="Start the API server.")

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    try:
        storage_backend = SQLiteStorage(config.DATA_DIR / "festival.db")
        seed_database(storage_backend)

        festival_manager = FestivalManager.from_storage(storage_backend)

        match args.command:
            case None:
                cli_prompts.display_festival_info(festival_manager)
            case "venues":
                cli_prompts.display_venues(festival_manager)
            case "programme":
                cli_prompts.display_programme(
                    festival_manager, helpers.date_from_str(args.day), args.venue
                )
            case "artists":
                if args.add:
                    cli_prompts.add_artist(festival_manager)
                elif args.focus:
                    cli_prompts.display_artist_info(festival_manager, args.focus)
                else:
                    display_artists(festival_manager)
            case "now":
                cli_prompts.display_performances_now(festival_manager, args.moment)
            case "add":
                add_performance(festival_manager, args.kind)
            case "cancel":
                cli_prompts.cancel_performance(festival_manager, args.id)
            case "interactive":
                from deauville_festival.cli_interactive import run

                run(festival_manager)
            case "serve":
                import uvicorn

                from deauville_festival.api.app import create_app

                app = create_app(storage_backend)
                uvicorn.run(app, host="0.0.0.0")  # noqa: S104
            case _:
                parser.print_help()
        return 0
    except (ValueError, errors.FestivalError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
