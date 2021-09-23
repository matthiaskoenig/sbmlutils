"""Module for notes.

Notes can be written in markdown.

Markdown -> HTML (Markdown parser)

markdown-it-py

"""
import re
import textwrap
from typing import Any, Optional

import css_inline  # type: ignore
import libsbml
from lxml import etree
from lxml import html as html_lxml
from markdown_it import MarkdownIt

from sbmlutils import RESOURCES_DIR


# read stylesheet for inline styles
with open(RESOURCES_DIR / "github.css", "r") as f_css:
    css = f_css.read()


class Notes:
    """SBML notes."""

    def __init__(self, notes: str):
        """Initialize notes object."""

        # remove indentation
        md = textwrap.dedent(notes)

        # markdown to html
        mdit = MarkdownIt()
        html = mdit.render(md)

        # css inline (this replaces single tags such as <br />!)
        html_inline = css_inline.inline(html, extra_css=css)

        # close single tags
        doc = html_lxml.fromstring(html_inline)
        doc_bytes: bytes = etree.tostring(doc)
        html = doc_bytes.decode(encoding="utf-8")

        # remove the outer tags
        html = html.replace("<html><head/>", "")
        html = html.replace("</body></html>", "")

        def reverse_open_tags(match_obj: Any) -> Optional[str]:
            """Reorder pre and code tags to fix issues in XML nodes."""
            if match_obj.group() is not None:
                return f"<code{match_obj.group(4)}><pre{match_obj.group(2)}>"
            return None

        html = re.sub("(<pre)(.*)(><code)(.*)(>)", reverse_open_tags, html)
        html = html.replace("</code></pre>", "</pre></code>")
        html = html.replace("<body", '<body xmlns="http://www.w3.org/1999/xhtml"')
        html = html + "\n</body>"

        notes_str = html
        self.xml: libsbml.XMLNode = libsbml.XMLNode.convertStringToXMLNode(notes_str)
        if self.xml is None:
            raise ValueError(f"XMLNode could not be generated for:\n{notes_str}")

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.xml.toXMLString())
