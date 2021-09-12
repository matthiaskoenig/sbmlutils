"""Module for notes.

Notes can be written in markdown.

Markdown -> HTML (Markdown parser)

markdown-it-py

"""

import markdown
import inspect
import textwrap
import libsbml
import css_inline
from premailer import transform, Premailer

css = "h1 { color:blue; }"
css = ""

class Notes:
    """SBML notes."""

    def __init__(self, notes: str):
        """Initialize notes object."""

        # md = inspect.cleandoc(notes)
        md = textwrap.dedent(notes)
        print("-" * 80)
        print("--- markdown ---")
        print(md)
        print("-" * 80)

        # markdown replacement
        html = markdown.markdown(
            md,
            output_format="xhtml"
        )

        from pprint import pprint
        from markdown_it import MarkdownIt
        mdit = MarkdownIt()
        html = mdit.render(md)
        print("--- html ---")
        print(html)
        print("-" * 80)

        # css inline (removes single tags
        # html_inline = css_inline.inline(html, extra_css=css)
        # from lxml import html, etree

        # closing single tags
        # doc = html.fromstring(html_inline)
        # doc_bytes: bytes = etree.tostring(doc)
        # html_inline = doc_bytes.decode(encoding="utf-8")

        # remove the outer tags
        # html_inline = html_inline.replace("<html><head/><body>", "")
        # html_inline = html_inline.replace("</body></html>", "")

        # fix pre tags
        # html = html.replace("<pre><code>", "<pre><code>\n")
        # FIXME: handle code blocks with additional content (e.g classes

        import re
        def reverse_open_tags(match_obj):
            if match_obj.group() is not None:
                # return f"<code{match_obj.group()}><pre>"
                return f"<code{match_obj.group(2)}><pre>"
                # return f"<code><pre>"

        html = re.sub("(<pre><code)(.*)(>)", reverse_open_tags, html)

        # html = html.replace("<pre><code>", "<code><pre>")
        html = html.replace("</code></pre>", "</pre></code>")

        # wrap in body tag
        notes_str = "\n".join([
            '<body xmlns="http://www.w3.org/1999/xhtml">',
            html,
            '</body>'
        ])

        # print("-" * 80)
        # print(html)
        # print("-" * 80)
        print("--- html processed ---")
        print(html)
        print("-" * 80)

        self.xml: libsbml.XMLNode = libsbml.XMLNode.convertStringToXMLNode(notes_str)
        xml_str = self.xml.toXMLString()
        print("--- xml str ---")
        print(xml_str)
        print("*" * 80)

        if self.xml is None:
            raise ValueError(f"XMLNode could not be generated for:\n{notes_str}")

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.xml.toXMLString())



if __name__ == "__main__":
    import libsbml
    html = """
    # Test

        # H1
        ## H2
    """

    html = """
    ```python
    var = 1
    ```
    """

    notes = Notes(html)
    print("-" * 80)
    print(str(notes))
