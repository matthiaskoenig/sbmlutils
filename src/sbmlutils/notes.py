"""Module for notes."""

import markdown
import inspect
import libsbml


class Notes:
    """SBML notes."""

    def __init__(self, notes: str):
        """Initialize notes object."""
        md = inspect.cleandoc(notes)
        html = markdown.markdown(md)
        notes_str = "\n".join([
            '<body xmlns="http://www.w3.org/1999/xhtml">',
            html,
            '</body>'
        ])

        self.xml: libsbml.XMLNode = libsbml.XMLNode.convertStringToXMLNode(notes_str)
        if self.xml is None:
            raise ValueError(f"XMLNode could not be generated for:\n{notes}")

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.xml.toXMLString())



