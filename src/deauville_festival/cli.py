import argparse
import sys
from pathlib import Path

from deauville_festival import errors, helpers
from deauville_festival.festival import FestivalManager
from deauville_festival.models import Artist, SoloPerformance
from deauville_festival.storage import JSONFileStorage

_FILE_PATH = Path("data/festival.json")


def display_festival_info(manager: FestivalManager) -> None:
    """Displays basic information about the festival."""
    festival_info = manager.get_festival_info()
    print(
        f"{festival_info.name}\n"
        f"From {festival_info.first_day} to {festival_info.last_day}\n"
        f"{festival_info.venue_count} venues, "
        f"{festival_info.artist_count} artists, "
        f"{festival_info.performance_count} performances"
    )


def display_venues(manager: FestivalManager) -> None:
    """Displays information about the venues."""
    venues = manager.list_venues()
    print(f"Venues: {len(venues)}")
    for venue in venues:
        print(str(venue))

    total_capacity = sum(venue.capacity for venue in venues)
    print(f"Total: {total_capacity} seats")


def add_artist(manager: FestivalManager) -> None:
    """Prompts for details and adds a new artist."""
    name = helpers.guard_empty_str(input("Name: "), "name")
    bio = input("Bio: ")
    photo_url = input("Photo URL: ")

    artist = Artist(name=name, bio=bio, photo_url=photo_url)

    manager.add_artist(artist)
    print(f"Added: artist {artist.name} ({artist.slug}).")


def display_artists(manager: FestivalManager) -> None:
    """Displays information about all artists."""
    artists = manager.list_artists()
    print(f"Artists: {len(artists)}")
    if not artists:
        return

    labels = [str(artist) for artist in artists]
    max_label_len = max(len(label) for label in labels)

    for artist, label in zip(artists, labels, strict=True):
        count = len(manager.list_performances(artist_slug=artist.slug))
        s = "show" if count == 1 else "shows"
        print(f"{label:<{max_label_len}} | {count} {s}")


def display_artist_info(artist_slug: str, manager: FestivalManager) -> None:
    """Displays details and performances for a specific artist."""
    artist, performances = manager.get_artist_with_performances(artist_slug)

    print(f"{artist.name} ({artist.slug})\n")
    print("About")
    print("-----")
    print(f"{artist.bio}\n")

    print("Performances")
    print("------------")

    if not performances:
        print("No performances found for this artist.")
        return

    venue_name_map = manager.get_venue_slug_to_name_map()
    venue_name_max_len = max(len(name) for name in venue_name_map.values())

    for performance in performances:
        start_time = performance.start
        end_time = performance.end
        role = performance.involves_artist(artist_slug)
        venue_name = venue_name_map[performance.venue]
        print(
            f"{start_time:%a %d %H:%M}-{end_time:%H:%M} | "
            f"{venue_name:<{venue_name_max_len}} | "
            f"{performance.title} ({role})"
        )


def display_programme(day: str, manager: FestivalManager) -> None:
    """Displays the programme for a specific day."""
    chosen_date = helpers.date_from_str(day)
    if not manager.is_in_range(chosen_date):
        raise ValueError(
            f"Date must be within the festival days\n"
            f"{', '.join(str(d) for d in manager.get_festival_days())}."
        )

    performances = manager.list_performances(chosen_date)
    if not performances:
        print(f"No performances found for {chosen_date}.")
        return

    venue_name_map = manager.get_venue_slug_to_name_map()
    venue_name_max_len = max(len(name) for name in venue_name_map.values())

    print(f"Programme for {chosen_date:%A %d %B}:")
    for performance in performances:
        start_time = performance.start
        end_time = performance.end
        venue_name = venue_name_map[performance.venue]
        print(
            f"{start_time:%H:%M}-{end_time:%H:%M} | "
            f"{venue_name:<{venue_name_max_len}} | "
            f"{performance.title} ({performance.kind})"
        )


def display_performances_now(moment_text: str, manager: FestivalManager) -> None:
    """Displays the performances happening now."""
    moment = helpers.datetime_from_str(moment_text)

    ongoing_performances, next_3_performances = manager.get_performance_lineup(moment)

    venue_name_map = manager.get_venue_slug_to_name_map()

    print(f"On stage at {moment:%Y-%m-%d %H:%M}:")
    if not ongoing_performances:
        print(f"\tNo performances happening at {moment:%Y-%m-%d %H:%M}.")
    else:
        for performance in ongoing_performances:
            end_time = performance.end
            venue_name = venue_name_map[performance.venue]
            print(f"- {performance.title} at {venue_name}, until {end_time:%H:%M}")

    print("Up next:")
    if not next_3_performances:
        print("No upcoming performances.")
    else:
        venue_name_max_len = max(len(name) for name in venue_name_map.values())
        for performance in next_3_performances:
            start_time = performance.start
            end_time = performance.end
            venue_name = venue_name_map[performance.venue]
            print(
                f"{start_time:%H:%M}-{end_time:%H:%M} | "
                f"{venue_name:<{venue_name_max_len}} | "
                f"{performance.title} ({performance.kind})"
            )


def parse_duration(duration_str: str) -> int:
    """Parses the duration input string into an integer."""
    duration_str = helpers.guard_empty_str(duration_str, "duration")
    if not duration_str.isdigit():
        raise ValueError(f"'{duration_str}' is not a valid number of minutes.")
    return int(duration_str)


def add_performance(manager: FestivalManager) -> None:
    """Prompts for details and adds a solo performance to the festival."""
    title = helpers.guard_empty_str(input("Title: "), "title")
    artist_slug = helpers.guard_empty_str(input("Artist (slug): "), "artist slug")
    venue_slug = helpers.guard_empty_str(input("Venue (slug): "), "venue slug")
    start = helpers.datetime_from_str(input("Start (YYYY-MM-DDTHH:MM): "))
    duration = parse_duration(input("Duration (minutes): "))

    performance = SoloPerformance(
        kind="solo",
        title=title,
        artist=artist_slug,
        venue=venue_slug,
        start=start,
        duration_minutes=duration,
    )

    manager.add_performance(performance)

    performance_festival_day = performance.get_festival_day()
    day_performances = manager.list_performances(day=performance_festival_day)
    line_number = day_performances.index(performance) + 1

    print(
        f"Added: {performance.id}, Event {line_number} of the programme {performance_festival_day}."
    )


def cancel_performance(id: str, manager: FestivalManager) -> None:
    """Cancels a performance by removing it from the list of performances."""
    performance_title = manager.delete_performance(id)
    print(f"Cancelled: {performance_title}")


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
        "day",
        help="The festival day (YYYY-MM-DD).",
    )

    artists_parser = subparsers.add_parser(
        "artists", help="Display information about the artists."
    )
    artists_parser.add_argument("--add", action="store_true", help="Add a new artist.")
    artists_parser.add_argument("--find", help="The slug of the artist.")

    now_parser = subparsers.add_parser(
        "now", help="Display the performances happening now."
    )
    now_parser.add_argument(
        "moment",
        help="The date and time (YYYY-MM-DDTHH:MM).",
    )

    subparsers.add_parser("add", help="Add a new performance.")

    cancel_parser = subparsers.add_parser("cancel", help="Cancel a performance.")
    cancel_parser.add_argument(
        "id",
        help="The ID of the performance (venue slug-start(YYYY-MM-DD-HHMM)).",
    )

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    try:
        storage_backend = JSONFileStorage(_FILE_PATH)
        manager = FestivalManager.from_storage(storage_backend)

        match args.command:
            case None:
                display_festival_info(manager)
            case "venues":
                display_venues(manager)
            case "programme":
                display_programme(args.day, manager)
            case "artists":
                if args.add:
                    add_artist(manager)
                elif args.find:
                    display_artist_info(args.find, manager)
                else:
                    display_artists(manager)
            case "now":
                display_performances_now(args.moment, manager)
            case "add":
                add_performance(manager)
            case "cancel":
                cancel_performance(args.id, manager)
            case _:
                parser.print_help()
        return 0
    except (ValueError, errors.FestivalError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
