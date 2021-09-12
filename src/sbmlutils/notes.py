"""Module for notes."""

import markdown
import inspect
import textwrap
import libsbml
import css_inline
from premailer import transform, Premailer

css = "h1 { color:blue; }"

class Notes:
    """SBML notes."""

    def __init__(self, notes: str):
        """Initialize notes object."""

        md = inspect.cleandoc(notes)
        md = textwrap.dedent(notes)
        html = markdown.markdown(
            md,
            output_format="xhtml"
        )

        # css inline (removes single tags
        html_inline = css_inline.inline(html, extra_css=css)
        from lxml import html, etree

        # closing single tags
        doc = html.fromstring(html_inline)
        doc_bytes: bytes = etree.tostring(doc)
        html_inline = doc_bytes.decode(encoding="utf-8")

        html_inline = html_inline.replace("<html><head/><body>", "")
        html_inline = html_inline.replace("</body></html>", "")

        import re


        # html_css = f"<html><head><style>{css}</style></head><body>" + html + "</body></html>"
        #
        #
        # p = Premailer(html_css)
        # html_inline = p.transform(pretty_print=False)
        # # match = re.match(r"<body>(.*)</body>", html_css)
        # # html_inline = match.group(0)
        # html_inline = html_inline.replace("<html><head></head><body>", "")
        # html_inline = html_inline.replace("</body></html>", "")


        notes_str = "\n".join([
            '<body xmlns="http://www.w3.org/1999/xhtml">',
            html_inline,
            '</body>'
        ])

        print("-" * 80)
        print(html)
        print("-" * 80)
        print(html_inline)
        print("-" * 80)

        self.xml: libsbml.XMLNode = libsbml.XMLNode.convertStringToXMLNode(notes_str)
        if self.xml is None:
            raise ValueError(f"XMLNode could not be generated for:\n{notes_str}")

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.xml.toXMLString())



