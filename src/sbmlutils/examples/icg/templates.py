"""Templates for icg model."""

from sbmlutils.examples import templates
from sbmlutils.factory import *


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
