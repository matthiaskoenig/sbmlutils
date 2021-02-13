"""Template information for the model creation."""
from datetime import datetime

import sbmlutils.factory as factory


# id : ('FamilyName', 'GivenName', 'Email', 'Organization')
creators = [
    factory.Creator(
        familyName="Koenig",
        givenName="Matthias",
        email="koenigmx@hu-berlin.de",
        organization="Humboldt-University Berlin, Institute for Theoretical Biology",
        site="https://livermetabolism.com",
    )
]

terms_of_use = """
    <div class="dc:provenance">The content of this model has been carefully created in a manual research effort.</div>
    <div class="dc:publisher">This file has been created by
    <a href="{site}" title="{given_name} {family_name}" target="_blank">{given_name} {family_name}</a>.</div>

    <h2>Terms of use</h2>
    <div class="dc:rightsHolder">Copyright © {year} {given_name} {family_name}.</div>
    <div class="dc:license">
        <p>Redistribution and use of any part of this model, with or without modification, are permitted provided
        that the following conditions are met:
        <ol>
          <li>Redistributions of this SBML file must retain the above copyright notice, this list of conditions and
          the following disclaimer.</li>
          <li>Redistributions in a different form must reproduce the above copyright notice, this list of conditions
          and the following disclaimer in the documentation and/or other materials provided
          with the distribution.</li>
        </ol>
        This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
        implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
        </p>
    </div>
""".format(
    year=datetime.now().year,
    given_name=creators[0].givenName,
    family_name=creators[0].familyName,
    site=creators[0].site,
)
