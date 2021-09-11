"""MyST examples."""

from myst_parser.main import to_html
from myst_parser.main import to_docutils
html = to_html("some *text*")

print(html)


with open("wealth_dynamics_md.md", "r") as f_in:
    md = f_in.read()
    # direct conversion to HTML (only handles core information)
    with open("wealth_dynamics_md_1.html", "w") as f_html:
        html = to_html(md)
        f_html.write(html)
    with open("wealth_dynamics_md.rst", "w") as f_rst:
        rst = to_docutils(md)
        print(rst)
        f_rst.write(rst)

    import docutils.core

    docutils.core.publish_file(
        source_path="wealth_dynamics_md.rst",
        destination_path="output.html",
        writer_name="html")
    #
    #
    # from docutils.core import publish_string
    # with open("wealth_dynamics_md_2.html", "w") as f_html:
    #     from myst_parser.main import to_docutils
    #     rst = to_docutils(md)
    #     html = publish_string(rst, writer_name='html')
    #     f_html.write(html)




