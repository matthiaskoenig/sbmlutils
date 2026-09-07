# COMBINE archives

A model is rarely the whole story: a study consists of one or more models, the simulation experiments which were run on them, the data and the figures. The [COMBINE archive](https://combinearchive.org/) (OMEX) packages all of it into one file with a `manifest.xml` which says what every entry is.

`sbmlutils` uses [pymetadata](https://matthiaskoenig.github.io/pymetadata/omex/) for archives; it is a dependency, so nothing extra has to be installed.

## Creating an archive

```python
from pathlib import Path

from pymetadata.omex import EntryFormat, ManifestEntry, Omex

from sbmlutils.factory import create_model

# create the models
sbml_path = Path("model.xml")
create_model(model=model, filepath=sbml_path)

# package them
omex = Omex()
omex.add_entry(
    entry_path=sbml_path,
    entry=ManifestEntry(
        location="./models/model.xml",
        format=EntryFormat.SBML_L3V1,
        master=True,
    ),
)
omex.to_omex(Path("study.omex"))
```

`location` is the path of the entry inside the archive, `format` is the identifiers.org URI of the format, and `master` marks the entry a tool should start with.

## Reading an archive

```python
from pymetadata.omex import Omex

with Omex.from_omex(Path("study.omex")) as omex:
    print(omex.manifest["./models/model.xml"].format)

    for entry in omex.entries_by_format("sbml"):
        print(entry.location, omex.get_path(entry.location))
```

The context manager removes the temporary directory the archive was extracted into.

`Omex.from_url` reads an archive directly from a URL, which is how the models of [BioModels](https://www.ebi.ac.uk/biomodels/) are fetched, see [Reading and writing](io.md#downloading-from-biomodels).

## Reports for an archive

`SBMLDocumentInfo` describes a single model. For an archive, iterate the SBML entries and describe each of them, which is what the [report](reports.md) does:

```python
from pymetadata.omex import Omex

from sbmlutils.report.sbmlinfo import SBMLDocumentInfo

with Omex.from_omex(Path("study.omex")) as omex:
    for entry in omex.entries_by_format("sbml"):
        info = SBMLDocumentInfo.from_sbml(omex.get_path(entry.location))
        print(entry.location, len(info.to_json()))
```

## Example

`examples/combine_archive/omex_models.py` creates two models, flattens the hierarchical one and packages all three into an archive:

```bash
python -m examples.combine_archive.omex_models
```
