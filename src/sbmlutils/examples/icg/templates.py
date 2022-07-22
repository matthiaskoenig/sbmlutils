"""Templates for icg model."""

from sbmlutils.factory import *
from sbmlutils.examples import templates

creators = [
    Creator(
        familyName="Köller",
        givenName="Adrian",
        email="adriankl39@googlemail.com",
        organization="Humboldt-University Berlin, Institute for Theoretical Biology",
        orcid="",
    ),
] + templates.creators

terms_of_use = templates.terms_of_use
