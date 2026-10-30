import pytest

from deauville_festival.models import Artist, Venue


class TestArtistInit:
    """Tests for `Artist` initialization and normalization."""

    def test_valid_artist_creation(self) -> None:
        artist = Artist(
            name="Élodie Marchal",
            bio="Stand-up comedian from Paris.",
            photo_url="https://example.com/elodie.jpg",
        )
        assert artist.name == "Élodie Marchal"
        assert artist.bio == "Stand-up comedian from Paris."
        assert artist.photo_url == "https://example.com/elodie.jpg"

    def test_strips_whitespace_from_fields(self) -> None:
        artist = Artist(
            name="  Élodie Marchal \n",
            bio="\t Stand-up comedian from Paris.  ",
            photo_url="  https://example.com/elodie.jpg\t\n",
        )
        assert artist.name == "Élodie Marchal"
        assert artist.bio == "Stand-up comedian from Paris."
        assert artist.photo_url == "https://example.com/elodie.jpg"

    def test_positional_arguments_raise_type_error(self) -> None:
        with pytest.raises(TypeError):
            Artist(
                "Élodie Marchal",  # type: ignore[arg-type]
                "Stand-up comedian from Paris.",  # type: ignore[arg-type]
                "https://example.com/elodie.jpg",  # type: ignore[arg-type]
            )


class TestArtistSlug:
    """Tests for `Artist.slug`."""

    @pytest.mark.parametrize(
        ("name", "expected_slug"),
        [
            ("Élodie Marchal", "elodie-marchal"),
            ("Élodie  Marchal !", "elodie-marchal"),
            ("Hugo Vernier", "hugo-vernier"),
            ("  Jean-Luc & Co. 2 ", "jean-luc-co-2"),
        ],
    )
    def test_slug_computed_from_name(self, name: str, expected_slug: str) -> None:
        artist = Artist(
            name=name,
            bio="Artist bio",
            photo_url="https://example.com/photo.jpg",
        )
        assert artist.slug == expected_slug


class TestArtistEqualityAndHash:
    """Tests for `Artist.__eq__` and `Artist.__hash__`."""

    def test_artists_with_same_slug_are_equal(self) -> None:
        artist_a = Artist(
            name="Élodie Marchal",
            bio="First bio",
            photo_url="https://example.com/a.jpg",
        )
        artist_b = Artist(
            name="elodie  marchal !",
            bio="Different bio",
            photo_url="https://example.com/b.jpg",
        )
        assert artist_a == artist_b
        assert hash(artist_a) == hash(artist_b)

    def test_artists_with_same_slug_deduplicate_in_set(self) -> None:
        artist_a = Artist(
            name="Élodie Marchal",
            bio="First bio",
            photo_url="https://example.com/a.jpg",
        )
        artist_b = Artist(
            name="ELODIE MARCHAL",
            bio="Second bio",
            photo_url="https://example.com/b.jpg",
        )
        assert len({artist_a, artist_b}) == 1

    def test_artists_with_different_slugs_are_not_equal(self) -> None:
        artist_a = Artist(
            name="Élodie Marchal",
            bio="Bio",
            photo_url="https://example.com/a.jpg",
        )
        artist_b = Artist(
            name="Hugo Vernier",
            bio="Bio",
            photo_url="https://example.com/a.jpg",
        )
        assert artist_a != artist_b

    @pytest.mark.parametrize(
        "other",
        [
            "elodie-marchal",
            None,
            42,
            {"name": "Élodie Marchal"},
            Venue(name="Élodie Marchal", capacity=100, address="Deauville"),
        ],
    )
    def test_artist_not_equal_to_non_artist_object(self, other: object) -> None:
        artist = Artist(
            name="Élodie Marchal",
            bio="Bio",
            photo_url="https://example.com/elodie.jpg",
        )
        assert artist != other


class TestArtistStr:
    """Tests for `Artist.__str__`."""

    def test_str_representation(self) -> None:
        artist = Artist(
            name="Élodie Marchal",
            bio="Stand-up comedian.",
            photo_url="https://example.com/elodie.jpg",
        )
        assert str(artist) == "Élodie Marchal (elodie-marchal)"
