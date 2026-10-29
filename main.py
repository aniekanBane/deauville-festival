import argparse
import dataclasses
import json
import sys
import typing
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from pathlib import Path

import helpers
from models import Artist, Performance, Venue

_FILE_PATH = Path("data/festival.json")


@dataclasses.dataclass
class FestivalData:
    name: str
    first_day: date
    last_day: date
    venues: list[Venue]
    artists: list[Artist]
    performances: list[Performance]


def festival_decoder(dict_data: dict[str, typing.Any]) -> dict[str, typing.Any]:
    if "first_day" in dict_data and "last_day" in dict_data:
        dict_data["first_day"] = date.fromisoformat(dict_data["first_day"])
    if "last_day" in dict_data:
        dict_data["last_day"] = date.fromisoformat(dict_data["last_day"])
    if "venues" in dict_data:
        dict_data["venues"] = [Venue(**venue) for venue in dict_data["venues"]]
    if "artists" in dict_data:
        dict_data["artists"] = [Artist(**artist) for artist in dict_data["artists"]]
    if "performances" in dict_data:
        dict_data["performances"] = [
            Performance(
                **{
                    **performance,
                    "start": datetime.fromisoformat(performance["start"]),
                }
            )
            for performance in dict_data["performances"]
        ]

    return dict_data


def load_data(path: Path) -> FestivalData:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f, object_hook=festival_decoder)

        return FestivalData(**data)
    except FileNotFoundError:
        print(f"File not found: {path}.")
        raise
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file: {path} (line {e.lineno}).") from None


class FestivalDataJSONEncoder(json.JSONEncoder):
    @typing.override
    def default(self, o: object) -> typing.Any:
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return self._exclude_none(dataclasses.asdict(o))

        if isinstance(o, datetime):
            return o.isoformat(timespec="minutes")

        if isinstance(o, date):
            return o.isoformat()

        return super().default(o)

    @staticmethod
    def _exclude_none(value: typing.Any) -> typing.Any:
        if isinstance(value, dict):
            return {
                k: FestivalDataJSONEncoder._exclude_none(v)
                for k, v in value.items()
                if v is not None
            }
        elif isinstance(value, list):
            return [
                FestivalDataJSONEncoder._exclude_none(v) for v in value if v is not None
            ]
        else:
            return value


def save_data(festival_data: FestivalData, path: Path) -> None:
    """Saves the festival data to the JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            festival_data, f, cls=FestivalDataJSONEncoder, ensure_ascii=False, indent=2
        )


def get_festival_day(date: date) -> tuple[datetime, datetime]:
    """Returns the start and end datetime of a festival day."""
    day_start = datetime.combine(date, time(hour=6))
    day_end = day_start + timedelta(days=1)
    return day_start, day_end


def get_performance_day(performance: Performance) -> tuple[datetime, datetime]:
    """Returns the start and end datetime of the festival day for a performance."""
    day = performance.start.date()
    if performance.start.time() < time(hour=6):
        day -= timedelta(days=1)

    return get_festival_day(day)


def get_performances_for_day(
    performances: Sequence[Performance], day: date
) -> list[Performance]:
    """Returns the performances happening on a specific date."""
    day_start, day_end = get_festival_day(day)
    return [
        performance
        for performance in performances
        if day_start <= performance.start < day_end
    ]


def display_festival_info(festival: FestivalData) -> None:
    info = (
        f"{festival.name}\n"
        f"From {festival.first_day} to {festival.last_day}\n"
        f"{len(festival.venues)} venues, "
        f"{len(festival.artists)} artists, "
        f"{len(festival.performances)} performances\n"
    )
    print(info)


def display_venues(venues: Sequence[Venue]) -> None:
    print(f"Venues: {len(venues)}")
    for venue in venues:
        print(f"{venue.slug}: {venue.name} ({venue.address}), {venue.capacity} seats")

    total_capacity = sum(venue.capacity for venue in venues)
    print(f"Total: {total_capacity} seats\n")


def display_programme(date_text: str, festival: FestivalData) -> None:
    chosen_date = helpers.date_from_str(date_text)
    if not (festival.first_day <= chosen_date <= festival.last_day):
        print(
            f"Date must be within the festival days "
            f"({festival.first_day} to {festival.last_day})."
        )
        return

    day_start, day_end = get_festival_day(chosen_date)

    performances = (
        performance
        for performance in festival.performances
        if day_start <= performance.start < day_end
    )

    venue_names = {venue.slug: venue.name for venue in festival.venues}

    print(f"Programme for {chosen_date:%A %d %B}:")
    for performance in sorted(
        performances, key=lambda p: (p.start, venue_names[p.venue])
    ):
        start_time = performance.start
        end_time = performance.end
        venue_name = venue_names[performance.venue]
        print(
            f"{start_time:%H:%M}-{end_time:%H:%M} | {venue_name} | {performance.title} ({performance.kind})"
        )


def display_artists(artists: Sequence[Artist]) -> None:
    print(f"Artists: {len(artists)}")
    for artist in sorted(artists, key=lambda a: a.slug):
        print(f"{artist.slug}: {artist.name}")


def display_artist_performances(artist_slug: str, festival: FestivalData) -> None:
    matching_artist = next(
        (artist for artist in festival.artists if artist.slug == artist_slug),
        None,
    )

    if matching_artist is None:
        print(f"No artist '{artist_slug}'.")
        return

    artist_performances: list[tuple[Performance, str]] = []
    for performance in festival.performances:
        if performance.artist == artist_slug:
            artist_performances.append((performance, "artist"))
        elif performance.host == artist_slug:
            artist_performances.append((performance, "host"))
        elif performance.teacher == artist_slug:
            artist_performances.append((performance, "teacher"))
        elif performance.acts and artist_slug in performance.acts:
            artist_performances.append((performance, "act"))

    venue_names = {venue.slug: venue.name for venue in festival.venues}

    print(f"{matching_artist.name}")
    for performance, role in sorted(artist_performances, key=lambda x: x[0].start):
        start_time = performance.start
        end_time = performance.end
        venue_name = venue_names[performance.venue]
        print(
            f"{start_time:%a %d %H:%M}-{end_time:%H:%M} | {venue_name} | {performance.title} ({role})"
        )


def display_performances_now(moment_text: str, festival: FestivalData) -> None:
    try:
        moment = datetime.fromisoformat(moment_text)
    except ValueError:
        print(
            f"'{moment_text}' is not a valid date and time. "
            "Use YYYY-MM-DDTHH:MM format."
        )
        return

    ordered_performances = sorted(festival.performances, key=lambda p: p.start)

    ongoing_performances = [
        performance
        for performance in ordered_performances
        if performance.start <= moment < performance.end
    ]
    next_3_performances = [
        performance
        for performance in ordered_performances
        if performance.start > moment
    ][:3]

    venue_names = {venue.slug: venue.name for venue in festival.venues}

    print(f"On stage at {moment:%Y-%m-%d %H:%M}:")
    if not ongoing_performances:
        print(f"\tNo performances happening at {moment}.")
    else:
        for performance in ongoing_performances:
            start_time = performance.start
            end_time = performance.end
            venue_name = venue_names[performance.venue]
            print(f"- {performance.title} at {venue_name}, until {end_time:%H:%M}")

    print("Up next:")
    if not next_3_performances:
        print("No upcoming performances.")
    else:
        for performance in sorted(next_3_performances, key=lambda p: p.start):
            start_time = performance.start
            end_time = performance.end
            venue_name = venue_names[performance.venue]
            print(
                f"{start_time:%H:%M}-{end_time:%H:%M} | {venue_name} | {performance.title} ({performance.kind})"
            )


def get_artist(artist_slug: str, artists: Sequence[Artist]) -> Artist:
    """Returns the artist with the given slug, or raises a `ValueError` if not found."""

    artist_slug_clean = helpers.guard_empty_str(artist_slug, "artist slug")

    artist = next((a for a in artists if a.slug == artist_slug_clean), None)
    if artist is None:
        raise ValueError(f"No artist found with slug '{artist_slug_clean}'.")
    return artist


def get_venue(venue_slug: str, venues: Sequence[Venue]) -> Venue:
    """Returns the venue with the given slug, or raises a `ValueError` if not found."""
    venue_slug_clean = helpers.guard_empty_str(venue_slug, "venue slug")

    venue = next((v for v in venues if v.slug == venue_slug_clean), None)
    if venue is None:
        raise ValueError(f"No venue found with slug '{venue_slug_clean}'.")

    return venue


def validate_performance_start(start_str: str, festival: FestivalData) -> datetime:
    """Validates the start input and returns it as a datetime object."""
    start_str = helpers.guard_empty_str(start_str, "start")
    start = helpers.datetime_from_str(start_str)

    festival_day = start.date()
    if start.time() < time(hour=6):
        festival_day -= timedelta(days=1)

    if not (festival.first_day <= festival_day <= festival.last_day):
        raise ValueError(
            f"Start date must be within the festival days "
            f"({festival.first_day} to {festival.last_day})."
        )

    return start


def validate_performance_duration(duration_str: str) -> int:
    """Validates the duration input and returns it as an integer."""
    duration_str = helpers.guard_empty_str(duration_str, "duration")

    if not duration_str.isdigit():
        raise ValueError(f"'{duration_str}' is not a valid number of minutes.")

    duration = int(duration_str)
    if not (
        Performance.DURATION_MINUTES_MIN <= duration <= Performance.DURATION_MINUTES_MAX
    ):
        raise ValueError(
            f"Duration must be from {Performance.DURATION_MINUTES_MIN} "
            f"to {Performance.DURATION_MINUTES_MAX} minutes."
        )

    return duration


def get_performance_artists(performance: Performance) -> set[str]:
    """Returns all artist slugs involved in a performance."""
    artists = {
        artist
        for artist in (
            performance.artist,
            performance.host,
            performance.teacher,
        )
        if artist is not None
    }
    if performance.acts:
        artists.update(performance.acts)

    return artists


def validate_artist_performance(
    new_performance: Performance,
    existing_performances: Sequence[Performance],
    artists: Sequence[Artist],
) -> None:
    artist_name_map = {artist.slug: artist.name for artist in artists}
    required_break = timedelta(minutes=30)

    new_artist = get_performance_artists(new_performance)
    for existing_performance in existing_performances:
        shared_artists = new_artist & get_performance_artists(existing_performance)
        if not shared_artists:
            continue

        too_close = (
            new_performance.start < existing_performance.end + required_break
            and existing_performance.start < new_performance.end + required_break
        )

        if too_close:
            artists_slug = next(iter(shared_artists))
            artist_name = artist_name_map[artists_slug]
            raise ValueError(
                f"{artist_name} is on stage in '{existing_performance.title}'."
            )


def validate_venue_performance(
    new_performance: Performance,
    existing_performances: Sequence[Performance],
    venues: Sequence[Venue],
) -> None:
    venue_name_map = {venue.slug: venue.name for venue in venues}
    required_break = timedelta(minutes=30)

    for existing_performance in existing_performances:
        if existing_performance.venue != new_performance.venue:
            continue

        too_close = (
            new_performance.start < existing_performance.end + required_break
            and existing_performance.start < new_performance.end + required_break
        )

        if too_close:
            venue_name = venue_name_map[new_performance.venue]
            performance_title = existing_performance.title
            start_time = existing_performance.start
            end_time = existing_performance.end
            raise ValueError(
                f"{venue_name} is busy with '{performance_title}' "
                f"({start_time:%Y-%m-%d} {start_time:%H:%M}-{end_time:%H:%M})."
            )


def validate_performance(
    performance: Performance, existing_performances: Sequence[Performance]
) -> None:
    if any(
        existing_performance.id == performance.id
        for existing_performance in existing_performances
    ):
        raise ValueError(f"A performance with id '{performance.id}' already exists.")


def add_performance(festival: FestivalData) -> None:
    title = helpers.guard_empty_str(input("Title: "), "title")
    artist = get_artist(input("Artist (slug): "), festival.artists)
    venue = get_venue(input("Venue (slug): "), festival.venues)
    start = validate_performance_start(input("Start (YYYY-MM-DDTHH:MM): "), festival)
    duration = validate_performance_duration(input("Duration (minutes): "))

    performance = Performance(
        kind="solo",
        title=title,
        artist=artist.slug,
        venue=venue.slug,
        start=start,
        duration_minutes=duration,
    )

    validate_venue_performance(performance, festival.performances, festival.venues)
    validate_artist_performance(performance, festival.performances, festival.artists)
    validate_performance(performance, festival.performances)

    festival.performances.append(performance)
    save_data(festival, _FILE_PATH)

    performance_festival_day = performance.get_festival_day()
    day_performances = sorted(
        get_performances_for_day(festival.performances, performance_festival_day),
        key=lambda p: p.start,
    )

    line_number = day_performances.index(performance) + 1

    print(
        f"Added: {performance.id}, Event {line_number} of the programme {performance_festival_day}."
    )


def cancel_performance(id: str, performances: list[Performance]) -> None:
    """Cancels a performance by removing it from the list of performances."""
    performance = next((p for p in performances if p.id == id), None)
    if performance is None:
        raise ValueError(f"No performance found with id '{id}'.")

    performances.remove(performance)
    print(f"Cancelled: {performance.title}")


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
    artists_parser.add_argument("slug", nargs="?", help="The slug of the artist.")

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
        festival = load_data(_FILE_PATH)

        match args.command:
            case None:
                display_festival_info(festival)
            case "venues":
                display_venues(festival.venues)
            case "programme":
                display_programme(args.day, festival)
            case "artists":
                if args.slug:
                    display_artist_performances(args.slug, festival)
                else:
                    display_artists(festival.artists)
            case "now":
                display_performances_now(args.moment, festival)
            case "add":
                add_performance(festival)
            case "cancel":
                cancel_performance(args.id, festival.performances)
            case _:
                parser.print_help()
        return 0
    except ValueError as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
