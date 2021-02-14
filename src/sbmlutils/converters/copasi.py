"""Helpers to work with COPASI files."""
from pathlib import Path

import libsbml


def write_ids_to_names(input_path: Path, output_path: Path) -> None:
    """Write SBML ids as names."""
    doc = libsbml.readSBMLFromFile(str(input_path))  # type: libsbml.SBMLDocument
    elements = doc.getListOfAllElements()
    for element in elements:
        if element.isSetId():
            element.setName(element.id)

    libsbml.writeSBMLToFile(doc, str(output_path))
