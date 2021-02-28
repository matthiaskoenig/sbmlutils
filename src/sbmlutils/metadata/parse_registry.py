"""Create latest MIRIAM JSON.

https://www.ebi.ac.uk/miriam/main/export/xml/
"""
import json

import xmlschema  # type: ignore

from sbmlutils import RESOURCES_DIR


MIRIAM_JSON = RESOURCES_DIR / "IdentifiersOrg-Registry.json"


def create_miriam_json() -> None:
    """Parse the latest miriam information.

    :return:
    """
    # "Tue, 04 Jun 2019 15:31:52 GMT" -> 2019-06-04T15:31:52
    # date="2019-06-04T15:31:52" data-version="2019-04-05T10:42:00

    # xmlschema.validators.exceptions.XMLSchemaValidationError: failed validating 'http://www.fungalbarcoding.org/BioloMICS.aspx?Table=Fungal barcodes&Rec=$id&Fields=All&ExactMatch=T' with XsdPatternFacets(['\\S*$id\\S*']):
    # > http://www.fungalbarcoding.org/BioloMICS.aspx?$id

    xs = xmlschema.XMLSchema(str(RESOURCES_DIR / "MiriamXML.xsd"))
    d = xs.to_dict(str(RESOURCES_DIR / "IdentifiersOrg-Registry.xml"))
    # pprint(d['datatype'][1])

    datatypes = {}
    for entry in d["datatype"]:
        datatypes[entry["namespace"]] = {
            "id": entry["@id"],
            "pattern": entry["@pattern"],
            "name": entry["name"],
            "namespace": entry["namespace"],
            "definition": entry["definition"],
        }

    # pprint(datatypes)
    with open(MIRIAM_JSON, "w") as fp:
        json.dump(datatypes, fp)


if __name__ == "__main__":
    create_miriam_json()

    with open(MIRIAM_JSON, "r") as fp:
        d = json.load(fp)
    print(d)
