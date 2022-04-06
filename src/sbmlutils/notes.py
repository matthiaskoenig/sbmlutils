"""Module for notes.

Notes can be either written in markdown or HTML.
Markdown -> HTML conversion is performed using `markdown-it-py` for the conversion.
No styles for the display are inserted here.
"""
import textwrap
from enum import Enum

import libsbml
from markdown_it import MarkdownIt

from sbmlutils import log
from sbmlutils.console import console


logger = log.get_logger(__name__)


class NotesFormat(str, Enum):
    """Supported formats for Notes."""

    MARKDOWN = "markdown"
    HTML = "html"


class Notes:
    """SBML notes."""

    def __init__(self, notes: str, format: NotesFormat = NotesFormat.MARKDOWN):
        """Initialize notes object."""

        # remove indentation
        md = textwrap.dedent(notes)

        # markdown to html
        if format == NotesFormat.MARKDOWN:
            mdit = MarkdownIt()
            html = mdit.render(md)
        elif format == NotesFormat.HTML:
            html = notes
        else:
            raise ValueError(f"Invalid Notes format: '{format}'")

        # insert body text with namespace
        notes_str = f'<body xmlns="http://www.w3.org/1999/xhtml">\n{html}\n</body>'

        self.xml: libsbml.XMLNode = libsbml.XMLNode.convertStringToXMLNode(notes_str)
        if self.xml is None:
            logger.error(
                f"XMLNode could not be generated. Most likely syntax error in \n"
                f"'{notes_str}'."
            )
            raise ValueError(f"XMLNode could not be generated for:\n{notes_str}")

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.xml.toXMLString())


if __name__ == "__main__":
    notes = Notes("** Test")
    print(notes)
    print(notes.xml)
