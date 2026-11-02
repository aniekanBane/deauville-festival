from datetime import date, datetime
from typing import Any

import pytest

from deauville_festival.models import (
    Artist,
    LineupPerformance,
    SoloPerformance,
    Venue,
    WorkshopPerformance,
)


@pytest.fixture
def sample_festival_data() -> dict[str, Any]:
    return {
        "name": "Deauville Festival du Rire",
        "first_day": date(2027, 6, 10),
        "last_day": date(2027, 6, 13),
        "venues": [
            Venue(
                name="Théâtre des Planches",
                capacity=420,
                address="Place du Casino, Deauville",
            ),
            Venue(
                name="Le Kiosque",
                capacity=120,
                address="Promenade des Planches",
            ),
        ],
        "artists": [
            Artist(
                name="Élodie Marchal",
                bio="Stand-up comedian.",
                photo_url="https://example.com/elodie.jpg",
            ),
            Artist(
                name="Hugo Vernier",
                bio="Improviser.",
                photo_url="https://example.com/hugo.jpg",
            ),
            Artist(
                name="Camille Roux",
                bio="Satirist.",
                photo_url="https://example.com/camille.jpg",
            ),
        ],
        "performances": [
            SoloPerformance(
                title="Opening Night",
                venue="theatre-des-planches",
                start=datetime(2027, 6, 10, 20, 0),
                duration_minutes=60,
                description="Opening solo show.",
                artist="elodie-marchal",
                min_age=12,
            ),
            LineupPerformance(
                title="Gala du Rire",
                venue="theatre-des-planches",
                start=datetime(2027, 6, 11, 21, 0),
                duration_minutes=90,
                description="Lineup gala.",
                host="elodie-marchal",
                acts=["hugo-vernier", "camille-roux"],
            ),
            WorkshopPerformance(
                title="Improv Workshop",
                venue="le-kiosque",
                start=datetime(2027, 6, 12, 14, 0),
                duration_minutes=120,
                description="Learn improv.",
                teacher="hugo-vernier",
                max_participants=15,
                participants=["Alice", "Bob"],
            ),
        ],
    }
