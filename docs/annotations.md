# Annotations

An element named `glc` means nothing to a machine. MIRIAM annotations attach a qualifier — *what is the relation?* — and a resource — *which database entry?* — to a model element: "this species **is** [CHEBI:17234](https://identifiers.org/CHEBI:17234)".

`sbmlutils` uses the annotation data structures of [pymetadata](https://matthiaskoenig.github.io/pymetadata) and offers two ways to apply them: in the model definition, or from a spreadsheet onto an existing model.

## In the model definition

Every element accepts `annotations` as a list of `(qualifier, resource)` tuples and an `sboTerm`:

```python
from sbmlutils.factory import Compartment, Species
from sbmlutils.metadata import BQB, SBO

Compartment(
    sid="cyto",
    value=1.0,
    name="cytosol",
    sboTerm=SBO.PHYSICAL_COMPARTMENT,
    annotations=[
        (BQB.IS, "go/GO:0005829"),                       # cytosol
        (BQB.IS, "https://en.wikipedia.org/wiki/Cytosol"),
    ],
)

Species(
    sid="glc",
    compartment="cyto",
    initialConcentration=5.0,
    sboTerm=SBO.SIMPLE_CHEMICAL,
    annotations=[
        (BQB.IS, "chebi/CHEBI:17234"),  # glucose
        (BQB.IS, "vmhmetabolite/glc_D"),
    ],
)
```

A resource is written as `collection/term` (`chebi/CHEBI:17234`), as an identifiers.org URL, as a `urn:miriam:*` URN or as an arbitrary URL. pymetadata normalizes it to an identifiers.org compact identifier and validates the term against the [identifiers.org](https://identifiers.org) registry.

## Qualifiers

`BQB` (biological) and `BQM` (model) are the MIRIAM qualifiers, re-exported from pymetadata:

```python
from sbmlutils.metadata import BQB, BQM

BQB.IS, BQB.IS_VERSION_OF, BQB.HAS_PART, BQB.IS_PART_OF, BQB.OCCURS_IN
BQM.IS, BQM.IS_DESCRIBED_BY, BQM.IS_DERIVED_FROM
```

Use `BQB` for what a thing *is* in biology and `BQM` for what the *model* is, e.g. `(BQM.IS_DESCRIBED_BY, "pubmed/12345678")` on the model itself.

## SBO terms

The systems biology ontology says what role an element plays. The terms come from pymetadata and carry their label and definition, so an editor shows what a term means while it is completed:

```python
from sbmlutils.metadata import SBO

SBO.SIMPLE_CHEMICAL       # 'SBO_0000247'
SBO.SIMPLE_CHEMICAL.label # 'simple chemical'
SBO.SIMPLE_CHEMICAL.curie # 'SBO:0000247'
```

An `sboTerm` is written both as the `sboTerm` attribute and as an RDF annotation of the element.

## Creators

The people behind a model are recorded on the model:

```python
from sbmlutils.factory import Creator, Model

model = Model(
    sid="example",
    creators=[
        Creator(
            familyName="König",
            givenName="Matthias",
            email="koenigmx@hu-berlin.de",
            organization="Humboldt-University Berlin",
            site="https://livermetabolism.com",
            orcid="0000-0003-1725-179X",
        )
    ],
)
```

## From a spreadsheet

Annotating an existing model, or keeping the annotations of a large model outside the code, is done with an annotation file — an Excel sheet, a csv or a tsv — with one annotation per row:

| pattern | sbml_type | annotation_type | qualifier | resource | name |
| --- | --- | --- | --- | --- | --- |
| | document | rdf | BQM_IS | sbo/SBO:0000293 | non-spatial continuous framework |
| `^demo_\d+$` | model | rdf | BQM_IS | go/GO:0008152 | metabolic process |
| `^glc$` | species | rdf | BQB_IS | chebi/CHEBI:17234 | glucose |
| `^glc$` | species | formula | | C6H12O6 | |
| `^atp$` | species | charge | | -4 | |

- `pattern` is a regular expression matched against the ids of the elements of `sbml_type`, so one row annotates many elements. It is empty for the document.
- `sbml_type` is `document`, `model`, `unit`, `reaction`, `transporter`, `species`, `compartment`, `parameter`, `rule` or `fbc:geneproduct`.
- `annotation_type` is `rdf` for a MIRIAM annotation, or `formula` and `charge`, which write the chemical formula and the charge through the fbc species plugin.
- `name` is a comment for the reader, it is not written into the model.

The file is applied to a model with `annotate_sbml`:

```python
from pathlib import Path

from sbmlutils.metadata.annotator import annotate_sbml

annotate_sbml(
    source=Path("model.xml"),
    annotations_path=Path("annotations.xlsx"),
    filepath=Path("model_annotated.xml"),
)
```

`create_model` takes the same file directly, so a model is annotated while it is created:

```python
from sbmlutils.factory import create_model

create_model(model=model, filepath=Path("model.xml"), annotations=Path("annotations.xlsx"))
```

## Validating annotations

`validate_sbml_annotations` checks every annotation of a model against the identifiers.org registry and returns the ones which do not resolve:

```python
from sbmlutils.metadata.validator import validate_sbml_annotations

df = validate_sbml_annotations("model.xml")
print(df)
```

This queries the registry, so it needs network access on the first run; pymetadata caches the responses.
