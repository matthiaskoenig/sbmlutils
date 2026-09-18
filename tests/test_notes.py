"""Testing notes."""

import logging
import re

import libsbml
import pytest

from sbmlutils.factory import Document, Model, Parameter, _xhtml_body_content
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


def test_xhtml_body_content_self_closing_body_logs_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a self-closing body without a closing tag is handled loudly.

    `<body .../>` has no `</body>` to search for. The empty result is
    correct (a self-closed body has no content), but it must be reached
    through an explicit guard and a logged warning rather than by accident
    of the slice indices, so that genuinely malformed input is not silently
    swallowed.
    """
    notes = '<body xmlns="http://www.w3.org/1999/xhtml"/>'
    with caplog.at_level(logging.WARNING, logger="sbmlutils"):
        content = _xhtml_body_content(notes)
    assert content == ""
    assert any("</body>" in record.getMessage() for record in caplog.records)


def _make_model() -> Model:
    """Create a minimal model for `Document` notes tests.

    Returns:
        a `Model` with only an `sid`, sufficient to construct a `Document`
    """
    return Model(sid="m1")


def test_document_notes_merges_markdown() -> None:
    """Test that Document merges user markdown notes with the attribution.

    The merged notes must be a single well formed body: the markdown must
    be rendered, the sbmlutils attribution must still be present, and the
    two fragments must not nest one body inside another.
    """
    doc = Document(model=_make_model(), notes="some **markdown**")
    assert doc.notes is not None
    assert doc.notes.count("<body") == 1
    assert "<strong>markdown</strong>" in doc.notes
    assert "Created with" in doc.notes

    sbml_doc = doc.create_sbml()
    assert sbml_doc.getNumErrors() == 0


def test_document_notes_merges_html_verbatim() -> None:
    """Test that Document merges user html notes without re-rendering them.

    Html notes must survive the merge untouched, next to the sbmlutils
    attribution, in a single body.
    """
    html = '<body xmlns="http://www.w3.org/1999/xhtml"><p>2*3*4</p></body>'
    doc = Document(model=_make_model(), notes=Notes(html, format=NotesFormat.HTML))
    assert doc.notes is not None
    assert doc.notes.count("<body") == 1
    assert "2*3*4" in doc.notes
    assert "<em>" not in doc.notes
    assert "Created with" in doc.notes

    sbml_doc = doc.create_sbml()
    assert sbml_doc.getNumErrors() == 0


def test_document_default_notes_are_rendered_html() -> None:
    """Test that the default sbmlutils attribution is rendered html.

    This pins the original bug: the attribution notice used to be stored as
    raw markdown and, once notes were normalized to xhtml at construction,
    it had to still come out as rendered html rather than literal markdown
    text such as `[https://...](...)`.
    """
    doc = Document(model=_make_model())
    assert doc.notes is not None
    assert doc.notes.count("<body") == 1
    assert '<a href="https://github.com/matthiaskoenig/sbmlutils">' in doc.notes
    assert "[https://github.com/matthiaskoenig/sbmlutils]" not in doc.notes

    sbml_doc = doc.create_sbml()
    assert sbml_doc.getNumErrors() == 0
