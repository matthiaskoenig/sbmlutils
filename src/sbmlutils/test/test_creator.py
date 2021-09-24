import pytest

from sbmlutils.factory import Creator


def test_creator_equality() -> None:
    """Test equality and hash."""

    c1 = Creator(
        familyName="König",
        givenName="Matthias",
        email="konigmatt@googlemail.com",
        organization="Humboldt-University Berlin",
    )

    c2 = Creator(
        familyName="König",
        givenName="Matthias",
        email="konigmatt@googlemail.com",
        organization="Humboldt-University Berlin",
    )

    assert c1 == c2
    assert hash(c1) == hash(c2)
