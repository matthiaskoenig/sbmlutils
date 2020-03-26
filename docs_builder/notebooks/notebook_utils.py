from IPython.core.display import HTML
from pygments import highlight
from pygments.lexers import XmlLexer
from pygments.formatters import HtmlFormatter
import IPython

def print_xml(xml_str: str):
    formatter = HtmlFormatter()
    IPython.display.display(HTML('<style type="text/css">{}</style>    {}'.format(
        formatter.get_style_defs('.highlight'),
        highlight(xml_str, XmlLexer(), formatter))))