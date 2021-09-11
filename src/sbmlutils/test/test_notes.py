"""Test notes which could be """
import pytest
import libsbml
from sbmlutils.notes import Notes
from sbmlutils.factory import Parameter


def test_markdown_note():
    p = Parameter(
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
    doc = libsbml.SBMLDocument()
    model: libsbml.Model = doc.createModel()
    sbml_p: libsbml.Parameter = p.create_sbml(model)

    print("\n")
    print("-" * 80)
    print(p.notes)
    print("-" * 80)
    notes = Notes(p.notes)
    print(notes)
    print("-" * 80)
    sbml_notes = sbml_p.getNotesString()
    print("-" * 80)

    assert '<a href="https://example.com">https://example.com</a>' in sbml_notes
    assert '<h2>Heading 2</h2>' in sbml_notes
    assert '<img src="./test.png"/>' in sbml_notes


notes_data = [
    ("# test", "<h1>test</h1>"),
    ("## test", "<h2>test</h2"),
    ('<p>test</p>', '<p>test</p>'),
]


@pytest.mark.parametrize("note,expected", notes_data)
def test_note(note: str, expected: str):
    note = Notes(note)
    note_str = str(note)
    assert expected in note_str

