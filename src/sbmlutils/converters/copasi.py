"""Helpers to work with COPASI files."""

from pathlib import Path

import libsbml

from sbmlutils.io import read_sbml, write_sbml
from sbmlutils.utils import all_elements


def write_ids_to_names(input_path: Path, output_path: Path) -> None:
    """Write SBML ids as names.

    Args:
        input_path: path of the SBML file to read
        output_path: path of the SBML file to write

    Raises:
        ValueError: if the input file cannot be read, see `read_sbml`
        OSError: if the output file cannot be written, see `write_sbml`
    """
    doc: libsbml.SBMLDocument = read_sbml(input_path)
    for element in all_elements(doc):
        if element.isSetId():
            element.setName(element.getId())

    write_sbml(doc, filepath=output_path)
