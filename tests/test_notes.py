"""Testing notes."""

import re

import libsbml
import pytest

from sbmlutils.factory import Parameter
from sbmlutils.notes import Notes, NotesFormat, detect_format


@pytest.mark.parametrize(
    "pattern",
    [
        '<a href="https://example.com">https://example.com</a>',
        "<h2.*>Heading 2</h2>",
        '<img src="./tests.png"/>',
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

        <img src="./tests.png" />
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
    ("# tests", "<h1.*>tests</h1>"),
    ("## tests", "<h2.*>tests</h2>"),
    ("### tests", "<h3.*>tests</h3>"),
    ("#### tests", "<h4.*>tests</h4>"),
    ("##### tests", "<h5.*>tests</h5>"),
    ("###### tests", "<h6.*>tests</h6>"),
    # emphasize
    ("*asterisks*", r"<p.*>[.\s]*<em>asterisks</em>[s\s]*</p>"),
    ("_underscore_", r"<p.*>[\s]*<em>underscore</em>[\s]*</p>"),
    ("**asterisks**", r"<p.*>[\s]*<strong>asterisks</strong>[\s]*</p>"),
    ("__underscores__", r"<p.*>[\s]*<strong>underscores</strong>[\s]*</p>"),
    ("<p>tests</p>", "<p.*>tests</p>"),
    # lists
    (
        """
    1. First item
    2. Second item
    """,
        r"<ol.*>[\s]*<li.*>First item</li>[\s]*<li.*>Second item</li>[\s]*</ol>",
    ),
    (
        """
    * First item
    * Second item
    """,
        r"<ul.*>[\s]*<li.*>First item</li>[\s]*<li.*>Second item</li>[\s]*</ul>",
    ),
    (
        """
    - item
    """,
        r"<ul.*>[\s]*<li.*>item</li>[\s]*</ul>",
    ),
    (
        """
    + item
    """,
        r"<ul.*>[\s]*<li.*>item</li>[\s]*</ul>",
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


def test_detect_format_markdown() -> None:
    """Test that a markdown string is detected as markdown."""
    assert detect_format("A **glucose** species") == NotesFormat.MARKDOWN


def test_detect_format_html() -> None:
    """Test that an XHTML string is detected as html."""
    notes = '<body xmlns="http://www.w3.org/1999/xhtml"><p>text</p></body>'
    assert detect_format(notes) == NotesFormat.HTML


def test_detect_format_leading_whitespace() -> None:
    """Test that leading whitespace does not hide the markup."""
    notes = '\n  <body xmlns="http://www.w3.org/1999/xhtml"><p>text</p></body>'
    assert detect_format(notes) == NotesFormat.HTML


def test_detect_format_markdown_with_inline_html() -> None:
    """Test that markdown which merely contains a tag stays markdown.

    Only a string which *starts* with markup is html, so a markdown
    paragraph using an inline tag is still rendered as markdown.
    """
    assert detect_format("see <b>this</b> value") == NotesFormat.MARKDOWN


def test_notes_html_is_not_rendered() -> None:
    """Test that html notes are stored verbatim.

    Markdown rendering mutates plain text, `2*3*4` becomes `2<em>3</em>4`,
    which must not happen to notes which came from an SBML file.
    """
    notes = '<body xmlns="http://www.w3.org/1999/xhtml"><p>2*3*4</p></body>'
    assert "2*3*4" in str(Notes(notes, format=NotesFormat.HTML))
    assert "<em>" not in str(Notes(notes, format=NotesFormat.HTML))
