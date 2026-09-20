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

The parent directory of `filepath` is created if it does not exist, and a write which fails all the same raises an `OSError` naming the path: a caller who asks for a file and gets none must not be told that the model is valid. This is about the file, not about the validation results, which are reported and never block.

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

The content of the fbc, distrib and comp packages comes along, see [The packages](#the-packages) below. A genome scale model keeps its bounds, its objective and its gene products:

```python
from pathlib import Path

from sbmlutils.factory import create_model
from sbmlutils.parser import sbml_to_model

model = sbml_to_model(Path("e_coli_core.xml"))
print(len(model.gene_products), len(model.objectives), model.strict)  # 137 1 True
create_model(
    model=model, filepath=Path("e_coli_core_out.xml"), sbml_level=3, sbml_version=2
)
```

### Measured coverage

The round trip is tested on the semantic cases of the [SBML test suite](https://github.com/sbmlteam/sbml-test-suite): each case is simulated with roadrunner, round tripped and simulated again, and the two trajectories are compared. The 1690 cases of SBML L3V2 come out as follows:

| Outcome | Cases |
| --- | --- |
| the round trip simulates like the original | 1465 |
| the round trip simulates differently: the file an external model definition references is not next to the round trip | 10 |
| the round trip simulates differently: an id shadows a MathML constant | 7 |
| roadrunner does not simulate the original: algebraic rules (108), delay equations (49), fbc (34), solver failures (3) | 194 |
| the original is not deterministic: events with the same or no priority fire at once, in random order | 14 |

So 1465 of the 1482 cases which can be compared round trip. Of those which use no package, 1362 of 1369 round trip, 99.5%; the other seven are the shadowed constants, see below. Of the comp cases, 103 of the 113 which can be compared round trip; the other ten reference a file which the comparison does not copy next to the document it writes. `scripts/roundtrip_report.py` runs this sweep, and `tests/test_roundtrip.py` lists every case which does not round trip yet with its reason.

### The packages

`sbml_to_model` reads the content of the fbc, distrib and comp packages, so it round trips with the rest of the model: flux bounds, objectives, gene products and their associations, charges and chemical formulas, key value pairs and user defined constraints; uncertainties with their parameters and spans, in the order of the document; submodels, ports, replaced elements, deletions, the whole nested `sBaseRef` chain of a reference, model definitions with everything inside them and external model definitions. What each package keeps and what it does not is on its own page: [Flux balance constraints](fbc.md#what-round-trips), [Distributions and uncertainties](distrib.md#what-round-trips) and [Model composition](comp.md#what-round-trips).

Simulation and validation cannot check this: roadrunner refuses to simulate fbc, ignores distrib and flattens comp away, and a document stripped of all three packages validates without an error. The round trip of the packages is therefore measured in three ways.

**Attribute by attribute.** The package content of the document read is compared with the package content of the document written, element by element and attribute by attribute, over 265 documents: the 157 SBML L3V2 test-suite cases which declare a package and 108 package files of `sbmlutils.resources`, among them `e_coli_core`, `Recon3D` and the whole-body model `icg_body`. Every construct of every package is preserved in every document which has it, with a single exception: the SBO terms of the `and` and `or` nodes of a gene product association, in two of the files, which the association string has no place for. The only differences accepted as equal are three normalizations which preserve the meaning: a nested group of the same operator in an association written back without the inner parentheses, a `<cn>` of integral value gaining `type="integer"`, and an annotation resource canonicalized to its compact identifiers.org URL.

**By simulating the flattened model.** For comp, the original and the round trip are flattened with `flatten_sbml` and simulated. All 113 of the 123 comp test-suite cases which roadrunner can simulate at all agree, as does `icg_body` with its external model definition; the other ten have an algebraic rule, a delay or a system the solver does not integrate, before the round trip as well as after.

**By solving the model.** For fbc, both documents are read as constraint based models with [cobrapy](https://cobrapy.readthedocs.io) and compared: the stoichiometric matrix, the flux bounds, the objective, the gene reaction rules, the genes and the metabolites, and the flux balance solution. `e_coli_core` and `Recon3D` agree in all of them and solve to the same objective value. Of the 34 fbc test-suite cases cobrapy loads 29, and all 29 agree; it refuses the other five as models, before and after the round trip.

The SBML test suite has no distrib case at all, so distrib is verified only on the files of this repository, which were written to show what `sbmlutils` can express and therefore test what their authors already believed. The fbc test-suite cases are uniform and carry no gene products, associations, user defined constraints or key value pairs; those come from `e_coli_core`, `Recon3D` and two example files. A nested `sBaseRef` occurs in three cases.

### What is not preserved

- **Math is normalized.** Math round trips through the infix notation of libsbml, so it comes back equivalent rather than identical: `<cn> 2 </cn>` becomes `<cn type="integer"> 2 </cn>`, and `a * (b * c)` one `<times/>` of three arguments. In the infix notation an id named like a MathML constant or csymbol, `pi`, `INF`, `NaN`, `time` or `avogadro`, cannot be told apart from the constant, so one of them comes back as the other.
- **The packages which are not modelled:** `groups`, `layout`, `render`, `qual`, `multi`, `spatial` and `arrays`. `sbml_to_model` declares the packages it reads, so neither the content of such a package nor its declaration survives a round trip.
- **An external model definition is a reference and stays one.** Its `source`, `modelRef` and `md5` come back unchanged and the file is never opened, so a hierarchical model has to be written next to the files it references, see [Model composition](comp.md#what-round-trips).
- **Annotation URIs are canonicalized.** The annotations are written through pymetadata, which writes a resource in its canonical form: `urn:miriam:pubmed:10659856` becomes `https://identifiers.org/pubmed:10659856`. This is intentional, and idempotent: round tripping the result again writes the same document. A resource whose collection the canonical form would lose is written exactly as it was read instead, and reported once for its collection, see [Annotations](annotations.md#resources-which-are-written-as-given).
- **Rules are grouped by kind.** A model keeps its assignment rules, rate rules and algebraic rules in a list each, so the round trip writes them in that order rather than in the order of the file. The order of the rules has no meaning in SBML.
- **Notes are wrapped into a body.** Notes which are a sequence of elements such as `<p>` are written inside a `<body>`, an equivalent form. Notes which are a `<body>` or a complete XHTML document rooted at `<html>` are kept as they are.
- **Inherited species units are made explicit.** A species without `substanceUnits` is written with the `substanceUnits` of the model, which it inherits anyway.
- **The model history** is not read. The document gains the notes in which `create_model` records that sbmlutils wrote it.

A round trip writes the SBML level and version `create_model` is given, which is L3V1 by default. The coverage above is measured writing L3V2, so only the L3V2 flavour of each test case is a true round trip. Reading an L1 or L2 file and writing L3 is a conversion: the model keeps its meaning, but not the file attribute for attribute.

The level and version decide what the document has a place for at all: a rule, a kinetic law, a trigger, a priority, a delay and a constraint have an `id` and a `name` only from L3V2 on, so writing such a model as L3V1 drops them. What a document cannot hold is reported once per kind of element and attribute, with how many elements it affected, an example and what to do about it:

```
The 'name' of 2 <assignmentRule> element(s) is not written: SBML L3V1 has no such attribute, e.g. 'AssignmentRule(the first rule)'. Write SBML Level 3 Version 2 to keep it.
```

The same is done for the version of a package, which decides whether a key value pair or a user defined constraint can be written at all. An attribute whose *value* libsbml refuses is a different matter and is reported for the element it is on.

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
