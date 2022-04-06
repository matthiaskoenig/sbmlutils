"""Template information for the model creation."""
from datetime import datetime

from sbmlutils.factory import Creator


creators = [
    Creator(
        familyName="König",
        givenName="Matthias",
        email="koenigmx@hu-berlin.de",
        organization="Humboldt-University Berlin, Institute for Theoretical Biology",
        site="https://livermetabolism.com",
        orcid="0000-0003-1725-179X",
    )
]

terms_of_use = """
    ## Terms of use
    The content of this model has been carefully created in a manual research effort.
    This file has been created by [{given_name} {family_name}]({site})
    using <a href="">[sbmlutils](https://github.com/matthiaskoenig/sbmlutils)</a>.
    For questions contact {email}.

    <a href="{site}">
    <img src="https://livermetabolism.com/img/people/koenig.png" width="80"></img>
    </a>
    Copyright © {year} {given_name} {family_name}.

    <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">
    <img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution 4.0 International License</a>.

    Redistribution and use of any part of this model, with or without modification,
    are permitted provided that the following conditions are met:

    1. Redistributions of this SBML file must retain the above copyright notice, this
       list of conditions and the following disclaimer.
    2. Redistributions in a different form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation and/or
       other materials provided with the distribution.

    This model is distributed in the hope that it will be useful, but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE.
""".format(
    year=datetime.now().year,
    given_name=creators[0].givenName,
    family_name=creators[0].familyName,
    email=creators[0].email,
    site=creators[0].site,
)
