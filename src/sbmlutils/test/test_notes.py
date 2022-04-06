"""Test notes which could be """
import re

import libsbml
import pytest

from sbmlutils.factory import Parameter
from sbmlutils.notes import Notes


@pytest.mark.parametrize(
    "pattern",
    [
        '<a href="https://example.com">https://example.com</a>',
        "<h2.*>Heading 2</h2>",
        '<img src="./test.png"/>',
    ],
)
def test_markdown_note(pattern: str) -> None:
    """Test creating a markdown note."""
    p = Parameter(
        "p1",
        value=1.0,
        notes="""
        # Markdown note
        Test this *text* in this `variable`.

            notes = Notes(c.notes)

        ## Heading 2
        <https://example.com>

        <img src="./test.png" />
        """,
    )
    doc = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    sbml_p: libsbml.Parameter = p.create_sbml(model)
    sbml_notes = sbml_p.getNotesString()

    match = re.search(pattern=pattern, string=sbml_notes)
    print(sbml_notes)
    assert match


notes_data = [
    # headings
    ("# test", "<h1.*>test</h1>"),
    ("## test", "<h2.*>test</h2>"),
    ("### test", "<h3.*>test</h3>"),
    ("#### test", "<h4.*>test</h4>"),
    ("##### test", "<h5.*>test</h5>"),
    ("###### test", "<h6.*>test</h6>"),
    # emphasize
    ("*asterisks*", r"<p.*>[.\s]*<em>asterisks</em>[s\s]*</p>"),
    ("_underscore_", r"<p.*>[\s]*<em>underscore</em>[\s]*</p>"),
    ("**asterisks**", r"<p.*>[\s]*<strong>asterisks</strong>[\s]*</p>"),
    ("__underscores__", r"<p.*>[\s]*<strong>underscores</strong>[\s]*</p>"),
    ("<p>test</p>", "<p.*>test</p>"),
    # lists
    (
        """
    1. First item
    2. Second item
    """,
        "<ol.*>[\s]*<li.*>First item</li>[\s]*<li.*>Second item</li>[\s]*</ol>",
    ),
    (
        """
    * First item
    * Second item
    """,
        "<ul.*>[\s]*<li.*>First item</li>[\s]*<li.*>Second item</li>[\s]*</ul>",
    ),
    (
        """
    - item
    """,
        "<ul.*>[\s]*<li.*>item</li>[\s]*</ul>",
    ),
    (
        """
    + item
    """,
        "<ul.*>[\s]*<li.*>item</li>[\s]*</ul>",
    ),
]


@pytest.mark.parametrize("note, expected", notes_data)
def test_note_markdown(note: str, expected: str) -> None:
    """Test note HTML creation from markdown."""
    notes = Notes(note)
    notes_str = str(notes)
    match = re.search(pattern=expected, string=notes_str)
    assert match


@pytest.mark.parametrize("notes, expected", notes_data)
def test_note_sbml(notes: str, expected: str) -> None:
    """Test note setting on SBML object."""
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    p = Parameter("p1", notes=notes)
    p_sbml: libsbml.Parameter = p.create_sbml(model=model)
    assert p_sbml
    assert p_sbml.isSetNotes()
