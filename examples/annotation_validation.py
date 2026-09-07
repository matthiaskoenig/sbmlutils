"""Validation of the annotations of a model.

`sbmlutils.metadata.validator.validate_sbml_annotations` checks every
annotation of a model against the identifiers.org registry and reports the ones
which do not resolve.

Run it from the root of the repository:

```bash
python -m examples.annotation_validation
```
"""

import pandas as pd

from sbmlutils.metadata.validator import validate_sbml_annotations
from sbmlutils.resources import MODELS_DIR


if __name__ == "__main__":
    sbml_faure2006 = MODELS_DIR / "qual" / "Faure2006_MammalianCellCycle.sbml"
    results: pd.DataFrame = validate_sbml_annotations(sbml_faure2006)
