# Reading and writing

`sbmlutils.io` wraps the libsbml reader and writer, so a model is read from a path, a string or a URL and written with the metadata SBML expects.

## Reading

```python
from sbmlutils.io import read_sbml

doc = read_sbml("model.xml")  # a path
doc = read_sbml(sbml_str)  # an SBML string
doc = read_sbml("https://.../model.xml")  # a URL
```

`read_sbml` returns a libsbml `SBMLDocument`. It validates on request:

```python
from sbmlutils.validation import ValidationOptions

doc = read_sbml(
    "model.xml",
    validate=True,
    validation_options=ValidationOptions(units_consistency=False),
)
```

Compressed files are read as they are: a `.xml.gz` path is decompressed transparently.

## Writing

```python
from sbmlutils.io import write_sbml

write_sbml(doc, filepath="model.xml")
sbml_str = write_sbml(doc, filepath=None)  # returns the SBML as a string
```

`write_sbml` records how the file was created in the notes of the document, and validates the result when asked to.

## Reading a model definition back

`sbml_to_model` parses an SBML file into the `Model` object of the [model creation](creation.md), which is the inverse of `create_model`:

```python
from sbmlutils.parser import sbml_to_model

model = sbml_to_model("model.xml")
print(model.species[0].sid)
```

This is how an existing model is brought into a python definition which can be edited, composed or generated from.

## Round tripping

`sbml_to_model` and `create_model` compose: a round trip `SBML -> sbml_to_model -> create_model -> SBML` preserves SBML core. A model read from a file can be changed in python and written back without losing what the file had:

```python
from pathlib import Path

from sbmlutils.factory import create_model
from sbmlutils.parser import sbml_to_model

model = sbml_to_model(Path("model.xml"))
model.parameters[0].value = 2.0
create_model(
    model=model, filepath=Path("model_changed.xml"), sbml_level=3, sbml_version=2
)
```

The round trip preserves the unit definitions and every unit reference, the function definitions, compartments, species and parameters, the reactions with their species references, modifiers and kinetic laws with local parameters, the initial assignments, rules, events with their trigger, priority, delay and event assignments, and constraints, and the id, name, metaid, sboTerm, notes and annotations of each of them. An element without math, which SBML allows from L3V2 on, such as a rule, an event assignment, a kinetic law, the trigger, priority or delay of an event, or an event without a trigger, round trips without math. Writing a model which was read from a file does not log the authoring hints of `create_model`, such as `'name' should be set`: the model has what its file had.

### Measured coverage

The round trip is tested on the semantic cases of the [SBML test suite](https://github.com/sbmlteam/sbml-test-suite): each case is simulated with roadrunner, round tripped and simulated again, and the two trajectories are compared. The 1690 cases of SBML L3V2 come out as follows:

| Outcome | Cases |
| --- | --- |
| the round trip simulates like the original | 1372 |
| the round trip simulates differently: the comp package | 103 |
| the round trip simulates differently: an id shadows a MathML constant | 7 |
| roadrunner does not simulate the original: algebraic rules (108), delay equations (49), fbc (34), solver failures (3) | 194 |
| the original is not deterministic: events with the same or no priority fire at once, in random order | 14 |

So 1372 of the 1482 cases which can be compared round trip. Of those which use no package, 1362 of 1369 round trip, 99.5%; the other seven are the shadowed constants, see below. `scripts/roundtrip_report.py` runs this sweep, and `tests/test_roundtrip.py` lists every case which does not round trip yet with its reason.

### What is not preserved

- **The fbc, distrib and comp packages.** Their content is not read: flux bounds, objectives and gene products, uncertainties, submodels, ports, replacements and deletions. A round trip keeps the package declaration but not the content, a comp model loses its submodels. The packages are out of scope of this release and are tracked separately.
- **Math is normalized.** Math round trips through the infix notation of libsbml, so it comes back equivalent rather than identical: `<cn> 2 </cn>` becomes `<cn type="integer"> 2 </cn>`, and `a * (b * c)` one `<times/>` of three arguments. In the infix notation an id named like a MathML constant or csymbol, `pi`, `INF`, `NaN`, `time` or `avogadro`, cannot be told apart from the constant, so one of them comes back as the other.
- **Annotation URIs are canonicalized.** The annotations are written through pymetadata, which writes a resource in its canonical form: `urn:miriam:pubmed:10659856` becomes `https://identifiers.org/pubmed:10659856`. This is intentional, and idempotent: round tripping the result again writes the same document.
- **Rules are grouped by kind.** A model keeps its assignment rules, rate rules and algebraic rules in a list each, so the round trip writes them in that order rather than in the order of the file. The order of the rules has no meaning in SBML.
- **Notes are wrapped into a body.** Notes which are a sequence of elements such as `<p>` are written inside a `<body>`, an equivalent form. Notes which are a `<body>` or a complete XHTML document rooted at `<html>` are kept as they are.
- **Inherited species units are made explicit.** A species without `substanceUnits` is written with the `substanceUnits` of the model, which it inherits anyway.
- **The model history** is not read. The document gains the notes in which `create_model` records that sbmlutils wrote it.

A round trip writes the SBML level and version `create_model` is given, which is L3V1 by default. The coverage above is measured writing L3V2, so only the L3V2 flavour of each test case is a true round trip. Reading an L1 or L2 file and writing L3 is a conversion: the model keeps its meaning, but not the file attribute for attribute.

## Antimony

[Antimony](https://tellurium.readthedocs.io/en/latest/antimony.html) is a compact text notation for models. `sbmlutils.parser` converts it to SBML, and to a model definition:

```python
from sbmlutils.parser import antimony_to_model, antimony_to_sbml

sbml_str = antimony_to_sbml("""
model example
    J0: S1 -> S2; k1*S1
    S1 = 10; S2 = 0; k1 = 0.1
end
""")

model = antimony_to_model("model.ant")
```

Both accept the antimony as a string or as a path to an `.ant` file.

The other direction, SBML to antimony, is `sbml_to_antimony` in `sbmlutils.io`, which accepts an SBML string or the path to an SBML file. `create_model` writes it next to the SBML file with `create_antimony=True`, see [Model creation](creation.md).

```python
from sbmlutils.io import sbml_to_antimony

ant_str = sbml_to_antimony(Path("model.xml"))
```

## Promoting local parameters

Local parameters of a kinetic law are invisible to most tools. `promote_local_variables` lifts them to the model, with the reaction id as a prefix:

```python
from sbmlutils.io.sbml import promote_local_variables

doc = promote_local_variables(doc, suffix="_promoted")
```

## Downloading from BioModels

`sbmlutils.biomodels` fetches models from [BioModels](https://www.ebi.ac.uk/biomodels/), as SBML or as a COMBINE archive:

```python
from pathlib import Path

from sbmlutils.biomodels import (
    download_biomodel_omex,
    download_biomodel_sbml,
    query_curated_biomodels,
)

# the OMEX archive of a model
download_biomodel_omex("BIOMD0000000012", Path("BIOMD0000000012.omex"))

# the SBML files inside it, written into a directory
paths = download_biomodel_sbml("BIOMD0000000012", Path("models"))

# the ids of all curated models
biomodel_ids = query_curated_biomodels()
```
