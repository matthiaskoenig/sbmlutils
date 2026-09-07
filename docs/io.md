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
