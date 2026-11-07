from datetime import date, datetime
from typing import Any

from deauville_festival import helpers
from deauville_festival.festival import FestivalManager
from deauville_festival.models import Artist


def display_festival_info(manager: FestivalManager) -> None:
    """Displays basic information about the festival."""
    festival_info = manager.get_festival_info()
    print(
        f"{festival_info.name}\n"
        f"From {festival_info.first_day} to {festival_info.last_day}\n"
        f"{festival_info.venue_count} venues, "
        f"{festival_info.artist_count} artists, "
        f"{festival_info.performance_count} performances."
    )


def display_venues(manager: FestivalManager) -> None:
    """Displays information about the venues."""
    venues = manager.list_venues()
    title = f"Venues: {len(venues)}"
    print(f"{title}\n{'-' * len(title)}")
    for venue in venues:
        print(str(venue))

    total_capacity = sum(venue.capacity for venue in venues)
    print(f"\nTotal: {total_capacity} seats")


def display_artist_info(manager: FestivalManager, artist_slug: str) -> None:
    """Displays details and performances for a specific artist."""
    artist, performances = manager.get_artist_with_performances(artist_slug)

    print(f"\n{artist.name} ({artist.slug})\n")
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


def display_programme(
    manager: FestivalManager,
    day: date | None = None,
    venue_slug: str | None = None,
) -> None:
    """Displays the programme filtered by day and/or venue."""
    performances = manager.list_performances(day=day, venue_slug=venue_slug)

    venue_name_map = manager.get_venue_slug_to_name_map()
    venue_label = (
        venue_name_map.get(venue_slug, "All venues") if venue_slug else "All venues"
    )
    day_label = day.strftime("%A %d %B") if day else "All days"

    title = f"Programme: {day_label} | {venue_label}"
    print(f"\n{title}\n{'-' * len(title)}")

    if not performances:
        print("No performances found for this selection.")
        return

    venue_name_max_len = max(len(name) for name in venue_name_map.values())

    for performance in performances:
        start_time = performance.start
        end_time = performance.end
        venue_name = venue_name_map.get(performance.venue, performance.venue)
        time_format = "%H:%M" if day else "%a %d %b %H:%M"
        time_str = f"{start_time:{time_format}}-{end_time:%H:%M}"
        print(
            f"{time_str} | "
            f"{venue_name:<{venue_name_max_len}} | "
            f"{performance.title} ({performance.kind})"
        )


def display_performances_now(
    manager: FestivalManager, moment: datetime | str | None = None
) -> None:
    """Displays the performances happening at a given moment and upcoming ones."""
    if isinstance(moment, str):
        moment = helpers.datetime_from_str(moment)
    else:
        moment = moment or datetime.now()

    ongoing_performances, next_3_performances = manager.get_performance_lineup(moment)
    venue_name_map = manager.get_venue_slug_to_name_map()

    title = f"On stage at {moment:%Y-%m-%d %H:%M}"
    print(f"\n{title}\n{'-' * len(title)}")
    if not ongoing_performances:
        print("No performances happening at the moment.")
    else:
        for performance in ongoing_performances:
            end_time = performance.end
            venue_name = venue_name_map.get(performance.venue, performance.venue)
            print(f"- {performance.title} at {venue_name}, until {end_time:%H:%M}")

    up_next_title = "Up next"
    print(f"\n{up_next_title}\n{'-' * len(up_next_title)}")
    if not next_3_performances:
        print("No upcoming performances.")
    else:
        venue_name_max_len = max(len(name) for name in venue_name_map.values())
        for performance in next_3_performances:
            start_time = performance.start
            end_time = performance.end
            venue_name = venue_name_map.get(performance.venue, performance.venue)
            time_str = (
                f"{start_time:%H:%M}-{end_time:%H:%M}"
                if start_time.date() == moment.date()
                else f"{start_time:%a %d %H:%M}-{end_time:%H:%M}"
            )
            print(
                f"{time_str} | "
                f"{venue_name:<{venue_name_max_len}} | "
                f"{performance.title} ({performance.kind})"
            )


def add_artist(manager: FestivalManager) -> None:
    """Prompts for details and adds a new artist."""
    name = Artist.validate_name(input("Name: "))
    bio = Artist.validate_bio(input("Bio: "))
    photo_url = Artist.validate_photo_url(input("Photo URL: "))

    artist = Artist(name=name, bio=bio, photo_url=photo_url)

    manager.add_artist(artist)
    print(f"Added artist: {str(artist)}.")


def display_performance_details(details: dict[str, Any]) -> None:
    """Displays detailed information about a single performance."""
    title = f"{details['title']} ({details['kind'].capitalize()})"
    print(f"\n{title}\n{'-' * len(title)}")
    print(f"ID:           {details['id']}")
    print(f"Venue:        {details['venue_name']}")
    start = details["start"]
    end = details["end"]
    print(
        f"Date & Time:  {start:%A %d %B %Y, %H:%M}-{end:%H:%M} "
        f"({details['duration_minutes']} min)"
    )
    print(f"Capacity:     {details.get('capacity', 'N/A')}")

    if details.get("summary"):
        print(f"Summary:      {details['summary']}")

    if details.get("description"):
        print(f"\nDescription:\n{details['description']}")

    kind = details.get("kind")
    if kind == "solo":
        min_age = details.get("min_age")
        if min_age:
            print(f"Min Age:      {min_age}+")
    elif kind == "workshop":
        if "places_left" in details:
            print(
                f"Places left:  {details['places_left']} / {details.get('max_participants')}"
            )
        participants = details.get("participants", [])
        if participants:
            print(f"Participants:  {', '.join(participants)}")

    artists = details.get("artists", [])
    if artists:
        artist_names = ", ".join(f"{a['name']} ({a['slug']})" for a in artists)
        print(f"Artists:       {artist_names}")


def cancel_performance(manager: FestivalManager, id: str) -> None:
    """Cancels a performance by removing it from the list of performances."""
    performance_title = manager.delete_performance(id)
    print(f"Cancelled: {performance_title}")


def parse_duration(duration_str: str) -> int:
    """Parses the duration input string into an integer."""
    duration_str = helpers.guard_empty_str(duration_str, "duration")
    if not duration_str.isdigit():
        raise ValueError(f"'{duration_str}' is not a valid number of minutes.")
    return int(duration_str)


def parse_min_age(min_age_str: str) -> int:
    """Parses the minimum age input string into an integer."""
    min_age_str = min_age_str.strip()
    if min_age_str and not min_age_str.isdigit():
        raise ValueError(f"'{min_age_str}' is not a valid number of years.")
    return int(min_age_str)


def parse_max_participants(max_participants_str: str) -> int:
    max_participants_str = helpers.guard_empty_str(
        max_participants_str, "max_participants"
    )
    if not max_participants_str.isdigit():
        raise ValueError(
            f"'{max_participants_str}' is not a valid number of participants."
        )
    return int(max_participants_str)
