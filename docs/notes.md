# Notes

SBML notes are the human readable description of an element. The specification requires them to be valid XHTML, which is unpleasant to write by hand.

`sbmlutils` accepts markdown and converts it, so the description is written the way documentation is written:

```python
from sbmlutils.factory import Model, Species

model = Model(
    sid="example",
    notes="""
    # Example model
    A model which demonstrates **notes**.

    ## Units
    - time: min
    - substance: mmole

    See [the SBML specification](https://sbml.org/documents/specifications/) for details.
    """,
    species=[
        Species(
            "glc",
            compartment="cell",
            initialConcentration=5.0,
            notes="D-glucose, the substrate of the model.",
        ),
    ],
)
```

The conversion uses [markdown-it-py](https://markdown-it-py.readthedocs.io) and supports the usual markdown: headings, lists, tables, links, emphasis and code. The result is wrapped in the `<body xmlns="http://www.w3.org/1999/xhtml">` element SBML expects.

## Notes directly

`Notes` converts a string on its own, which is useful when notes are set on an existing libsbml object:

```python
from sbmlutils.notes import Notes, NotesFormat

notes = Notes("# Heading\n\nSome *text*.")
sbase.setNotes(notes.xml)
```

`NotesFormat.HTML` passes the string through unchanged when it is already XHTML:

```python
Notes("<p>already xhtml</p>", format=NotesFormat.HTML)
```

## Reusable text blocks

Notes are plain strings, so shared text is a variable. The examples keep the terms of use in `examples/templates.py` and append it to the notes of every model:

```python
from examples import templates

model = Model(sid="example", notes="# Example model\n" + templates.terms_of_use)
```
