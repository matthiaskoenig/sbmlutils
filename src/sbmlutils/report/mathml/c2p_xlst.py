"""Content MathML to presentation MathML conversion.

A common problem in rendering MathML is that the content MathML is difficult to read.
The presentation MathML has a much better rendering and improves understandability.
This module uses stylesheets for the conversion of content MathMl -> presention MathML.

This is currently just a proof of principle.
Content MathML would improve readability of reports.

MathML is currently rendered with MathJax http://docs.mathjax.org/en/latest/.
see also https://docs.mathjax.org/en/v2.7-latest/options/extensions/Content-MathML.html

stylesheets: https://code.google.com/archive/p/web-xslt/wikis/Overview.wiki
see also: https://github.com/sympy/sympy/issues/11893
"""
import lxml.etree as et
from pathlib import Path


def transform_mathml(mathml: Path, stylesheet: Path):
    """Transform content to presentation mathml.

    :param mathml: Path to content MathML
    :param stylesheet: Path to stylesteet for transformation
    """
    dom = et.parse(str(mathml))
    xslt = et.parse(str(stylesheet))
    transform = et.XSLT(xslt)
    newdom = transform(dom)

    print(et.tostring(newdom, pretty_print=True))


if __name__ == "__main__":
    base_dir = Path(__file__).parent / "resources"
    xsl_filename = "ctop.xsl"
    transform_mathml(
        mathml=base_dir / "content_mathml.xml",
        stylesheet=base_dir / "ctop.xsl"
    )
