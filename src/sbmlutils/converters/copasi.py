"""Helpers to work with COPASI files."""

from pathlib import Path

import libsbml

from sbmlutils.io import read_sbml, write_sbml


def write_ids_to_names(input_path: Path, output_path: Path) -> None:
    """Write SBML ids as names."""
    doc: libsbml.SBMLDocument = read_sbml(input_path)
    elements = doc.getListOfAllElements()
    for element in elements:
        if element.isSetId():
            element.setName(element.getId())

    write_sbml(doc, filepath=output_path)
