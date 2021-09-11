"""Test notes which could be """
from sbmlutils.factory import *


def test_markdown_note():
    c = Parameter(
        "p1", value=1.0,
        notes="""
        # Markdown note
        Test this *text* in this `variable`.

            notes = Notes(c.notes)

        ## Heading 2
        <https://example.com>

        <img src="./test.png" />
        """
    )
    print("\n")
    print("-" * 80)
    print(c.notes)
    print("-" * 80)
    notes = Notes(c.notes)
    print(notes)
    print("-" * 80)


# FIXME: make all this markdown tests
# st.markdown("This **markdown** is awesome! :sunglasses:")
#
# st.markdown("This <b>HTML tag</b> is escaped!")
#
# st.markdown("This <b>HTML tag</b> is not escaped!", unsafe_allow_html=True)
#
# st.markdown("[text]")
#
# st.markdown("[link](href)")
#
# st.markdown("[][]")
#
# st.markdown("Inline math with $\KaTeX$")
#
# st.markdown(
#     """
# $$
# ax^2 + bx + c = 0
# $$
# """
# )
#
# st.markdown("# Some header 1")
# st.markdown("## Some header 2")
# st.markdown("### Some header 3")
#
# st.markdown(
#     """
# | Col1      | Col2        |
# | --------- | ----------- |
# | Some      | Data        |
# """
