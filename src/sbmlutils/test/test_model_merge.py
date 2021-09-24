import pytest

from sbmlutils.factory import *


def test_creator_merge():

    c = Creator(
        givenName="Matthias",
        familyName="König",
        organization="Humboldt-University Berlin",
        email="konigmatt@googlemail.com",
    )

    m1 = Model(
        "m1",
        creators=[c],
    )
    assert len(m1.creators) == 1

    m2 = Model("m2", creators=[c])
    assert len(m2.creators) == 1

    m_merged = Model.merge_models(models=[m1, m2])

    print("CREATORS:", m_merged.creators)

    assert len(m_merged.creators) == 1
