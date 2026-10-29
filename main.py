# Reads the data of the festival and prints its name.
# Run it from this folder: uv run main.py
#
# The three lines below open the file and turn its JSON text into Python
# dicts and lists. How they work is explained in step 05; for now, use them.

import argparse
import json
import re
import unicodedata
from datetime import date, datetime, time, timedelta
from typing import NamedTuple

from models import Artist, Performance, Venue


class FestivalData(NamedTuple):
    name: str
    first_day: date
    last_day: date
    venues: list[Venue]
    artists: list[Artist]
    performances: list[Performance]


def _load_festival_data(file_name: str = "data/festival.json") -> FestivalData:
    """Loads the festival data from a JSON file."""
    with open(file_name, encoding="utf-8") as file:
        data = json.load(file)

    venues: list[Venue] = [Venue(**venue) for venue in data["venues"]]
    artists: list[Artist] = [Artist(**artist) for artist in data["artists"]]
    performances: list[Performance] = [
        Performance(
            **{
                **performance,
                "start": datetime.fromisoformat(performance["start"]),
            }
        )
        for performance in data["performances"]
    ]

    return FestivalData(
        name=data["name"],
        first_day=date.fromisoformat(data["first_day"]),
        last_day=date.fromisoformat(data["last_day"]),
        venues=venues,
        artists=artists,
        performances=performances,
    )


def _get_slug(name: str) -> str:
    """Returns the slug of a given name."""
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9-]+", "-", ascii_name).strip("-")
    return slug


def display_festival_info(festival: FestivalData) -> None:
    info = (
        f"{festival.name}\n"
        f"From {festival.first_day} to {festival.last_day}\n"
        f"{len(festival.venues)} venues, "
        f"{len(festival.artists)} artists, "
        f"{len(festival.performances)} performances\n"
    )
    print(info)


def display_venues_info(venues: list[Venue]) -> None:
    for venue in venues:
        print(f"{_get_slug(venue.name)}: {venue.name}, {venue.capacity} seats")

    total_capacity = sum(venue.capacity for venue in venues)
    print(f"Total: {total_capacity} seats\n")


def display_programme(date_text: str, festival: FestivalData) -> None:
    try:
        chosen_date = date.fromisoformat(date_text)
    except ValueError:
        print(f"Invalid date: {date_text}. Use YYYY-MM-DD format.")
        return

    if not (festival.first_day <= chosen_date <= festival.last_day):
        print(
            f"Date must be within the festival days "
            f"({festival.first_day} to {festival.last_day})."
        )
        return

    day_start = datetime.combine(chosen_date, time(hour=6))
    day_end = day_start + timedelta(days=1)

    performances = (
        performance
        for performance in festival.performances
        if day_start <= performance.start < day_end
    )

    print(f"Programme for {chosen_date}:")
    for performance in sorted(performances, key=lambda p: p.start):
        start_time = performance.start.strftime("%H:%M")
        venue_name = next(
            (
                venue.name
                for venue in festival.venues
                if _get_slug(venue.name) == performance.venue
            ),
            performance.venue,
        )
        print(f"{start_time} | {venue_name} | {performance.title} ({performance.kind})")


def display_artist_performances(
    artist_slug: str,
    artists: list[Artist],
    performances: list[Performance],
    venues: list[Venue],
) -> None:
    matching_artist = next(
        (artist for artist in artists if _get_slug(artist.name) == artist_slug), None
    )

    if matching_artist is None:
        print(f"No artist '{artist_slug}'.")
        return

    artist_performances: list[tuple[Performance, str]] = []
    for performance in performances:
        if performance.artist == artist_slug:
            artist_performances.append((performance, "artist"))
        elif performance.host == artist_slug:
            artist_performances.append((performance, "host"))
        elif performance.teacher == artist_slug:
            artist_performances.append((performance, "teacher"))
        elif artist_slug in performance.acts:
            artist_performances.append((performance, "act"))

    print(f"{matching_artist.name}")
    for performance, role in sorted(artist_performances, key=lambda x: x[0].start):
        start_time = performance.start.strftime("%Y-%m-%d %H:%M")
        venue_name = next(
            (
                venue.name
                for venue in venues
                if _get_slug(venue.name) == performance.venue
            ),
            performance.venue,
        )
        print(f"{start_time} | {venue_name} | {performance.title} ({role})")


def _create_parser() -> argparse.ArgumentParser:
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
        "artist", help="Display information about an artist's performances."
    )
    artists_parser.add_argument("slug", help="The slug of the artist.")

    return parser


if __name__ == "__main__":
    parser = _create_parser()
    args = parser.parse_args()

    festival = _load_festival_data()

    if args.command is None:
        display_festival_info(festival)
    elif args.command == "venues":
        display_venues_info(festival.venues)
    elif args.command == "programme":
        display_programme(args.day, festival)
    elif args.command == "artist":
        display_artist_performances(
            args.slug, festival.artists, festival.performances, festival.venues
        )
