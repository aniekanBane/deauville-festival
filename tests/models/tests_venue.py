import pytest

from deauville_festival import errors
from deauville_festival.models import Artist, Venue


class TestVenueInit:
    """Tests for `Venue` initialization and validation."""

    def test_valid_venue_creation(self) -> None:
        venue = Venue(
            name="Théâtre des Planches",
            capacity=420,
            address="Place du Casino, Deauville",
        )
        assert venue.name == "Théâtre des Planches"
        assert venue.capacity == 420
        assert venue.address == "Place du Casino, Deauville"

    def test_strips_whitespace_from_name_and_address(self) -> None:
        venue = Venue(
            name="  Le Kiosque \n",
            capacity=120,
            address="\t Promenade des Planches  ",
        )
        assert venue.name == "Le Kiosque"
        assert venue.address == "Promenade des Planches"

    def test_zero_capacity_raises_invalid_error(self) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            Venue(name="Open Air", capacity=0, address="Beach")
        assert str(exc_info.value) == "Capacity must be a positive integer."

    @pytest.mark.parametrize("invalid_capacity", [-1, -10, -500])
    def test_non_positive_capacity_raises_invalid_error(
        self, invalid_capacity: int
    ) -> None:
        with pytest.raises(errors.InvalidError) as exc_info:
            Venue(
                name="Le Kiosque",
                capacity=invalid_capacity,
                address="Promenade des Planches",
            )

        assert str(exc_info.value) == "Capacity must be a positive integer."

    def test_positional_arguments_raise_type_error(self) -> None:
        with pytest.raises(TypeError):
            Venue("Le Kiosque", 120, "Promenade des Planches")  # type: ignore[misc]


class TestVenueSlug:
    """Tests for `Venue.slug`."""

    @pytest.mark.parametrize(
        ("name", "expected_slug"),
        [
            ("Le Kiosque", "le-kiosque"),
            ("Théâtre des Planches", "theatre-des-planches"),
            ("  Salon d'Honneur ! ", "salon-d-honneur"),
            ("Studio 42", "studio-42"),
        ],
    )
    def test_slug_computed_from_name(self, name: str, expected_slug: str) -> None:
        venue = Venue(name=name, capacity=100, address="Deauville")
        assert venue.slug == expected_slug


class TestVenueEqualityAndHash:
    """Tests for `Venue.__eq__` and `Venue.__hash__`."""

    def test_venues_with_same_slug_are_equal(self) -> None:
        venue_a = Venue(
            name="Théâtre des Planches",
            capacity=420,
            address="Place du Casino",
        )
        venue_b = Venue(
            name="theatre-des-planches!",
            capacity=100,
            address="Different Address",
        )
        assert venue_a == venue_b
        assert hash(venue_a) == hash(venue_b)

    def test_venues_with_same_slug_deduplicate_in_set(self) -> None:
        venue_a = Venue(name="Le Kiosque", capacity=120, address="Address 1")
        venue_b = Venue(name="LE KIOSQUE!", capacity=200, address="Address 2")
        assert len({venue_a, venue_b}) == 1

    def test_venues_with_different_slugs_are_not_equal(self) -> None:
        venue_a = Venue(name="Le Kiosque", capacity=120, address="Deauville")
        venue_b = Venue(name="Le Casino", capacity=120, address="Deauville")
        assert venue_a != venue_b

    @pytest.mark.parametrize(
        "other",
        [
            "le-kiosque",
            None,
            120,
            {"name": "Le Kiosque"},
            Artist(name="Le Kiosque", bio="Bio", photo_url="http://example.com/p.jpg"),
        ],
    )
    def test_venue_not_equal_to_non_venue_object(self, other: object) -> None:
        venue = Venue(name="Le Kiosque", capacity=120, address="Deauville")
        assert venue != other


class TestVenueStr:
    """Tests for `Venue.__str__`."""

    def test_str_representation(self) -> None:
        venue = Venue(
            name="Théâtre des Planches",
            capacity=420,
            address="Place du Casino",
        )
        assert (
            str(venue)
            == "theatre-des-planches: Théâtre des Planches (Place du Casino), 420 seats"
        )
