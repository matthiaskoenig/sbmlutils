"""
Handling Markdown information.


"""

st.markdown("This **markdown** is awesome! :sunglasses:")

st.markdown("This <b>HTML tag</b> is escaped!")

st.markdown("This <b>HTML tag</b> is not escaped!", unsafe_allow_html=True)

st.markdown("[text]")

st.markdown("[link](href)")

st.markdown("[][]")

st.markdown("Inline math with $\KaTeX$")

st.markdown(
    """
$$
ax^2 + bx + c = 0
$$
"""
)

st.markdown("# Some header 1")
st.markdown("## Some header 2")
st.markdown("### Some header 3")

st.markdown(
    """
| Col1      | Col2        |
| --------- | ----------- |
| Some      | Data        |
"""
