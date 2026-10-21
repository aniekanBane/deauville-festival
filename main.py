# Reads the data of the festival and prints its name.
# Run it from this folder: uv run main.py
#
# The three lines below open the file and turn its JSON text into Python
# dicts and lists. How they work is explained in step 05; for now, use them.

import json
import unicodedata
from datetime import datetime

from models import Artist, Performance, Venue


def display_venues_info(venues: list[Venue]) -> None:
    if not venues:
        return

    total_capacity = 0
    venue_lines = (
        f"- {venue.name}: {venue.capacity} seats ({venue.address})"
        for venue in venues
    )
    total_capacity = sum(venue.capacity for venue in venues)
    print(
        "Venues:\n"
        f"{'\n'.join(venue_lines)}\n"
        f"Total: {total_capacity} seats\n"
    )

def display_performances_info(performances: list[Performance]) -> None:
    if not performances:
        return

    kind_counts: dict[str, int] = {}
    le_kiosque_lines: list[str] = []
    workshop_lines: list[str] = []

    for performance in performances:
        kind_counts[performance.kind] = kind_counts.get(performance.kind, 0) + 1
        start_time = performance.start.strftime("%Y-%m-%d %H:%M")

        if performance.venue == "le-kiosque":
            le_kiosque_lines.append(f"- {start_time}: {performance.title}")

        if performance.kind == "workshop":
            workshop_lines.append(
                f"{performance.title} on ({start_time}): "
                f"{len(performance.participants)}/{performance.max_participants} registered"
            )

    lines = [f"{kind}: {count}" for kind, count in kind_counts.items()]
    lines.extend(["", "At Le Kiosque:"])
    lines.extend(le_kiosque_lines)

    longest_performance = max(performances, key=lambda p: p.duration_minutes)
    lines.extend([
        "",
        "Longest: "
        f"{longest_performance.title} ({longest_performance.duration_minutes} mins)"
    ])

    lines.extend([""] + workshop_lines)

    print("\n".join(lines))


def _normalize_artist_name(name: str) -> str:
    name = name.lower().replace(" ", "-")
    name = unicodedata.normalize("NFD", name)
    name = "".join(c for c in name if unicodedata.category(c) != "Mn")
    return name

def display_artists_info(artists: list[Artist], performances: list[Performance]) -> None:
    if not artists:
        return

    stage_appearances = {_normalize_artist_name(artist.name): 0 for artist in artists}
    for performance in performances:
        credited_artists = {
            performance.artist,
            performance.teacher,
            performance.host,
            *performance.acts,
        }
        for artist in credited_artists:
            if artist in stage_appearances:
                stage_appearances[artist] += 1

    most_appearances = max(stage_appearances.values(), default=0)
    most_appearing_artists = (
        artist
        for artist, apperances in stage_appearances.items()
        if  apperances == most_appearances
    )

    print(f"\nOn Stage {most_appearances} times:", ", ".join(most_appearing_artists))

if __name__ == "__main__":
    with open("data/festival.json", encoding="utf-8") as file:
        festival = json.load(file)
        venues: list[Venue] = [Venue(**venue) for venue in festival["venues"]]
        artists: list[Artist] = [Artist(**artist) for artist in festival["artists"]]
        performances: list[Performance] = [
            Performance(
                **{
                    **performance,
                    "start": datetime.fromisoformat(performance["start"]),
                }
            )
            for performance in festival["performances"]
        ]

    festival_info = (
        f"\n{festival['name']}\n"
        f"From {festival['first_day']} to {festival['last_day']}\n"
        f"{len(venues)} venues, {len(artists)} artists, "
        f"{len(performances)} performances\n"
    )
    print(festival_info)

    display_venues_info(venues)
    display_performances_info(performances)
    display_artists_info(artists, performances)
