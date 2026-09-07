# Reports

An SBML file is XML: complete, but not readable. A report answers the questions a modeller actually has about a model — which species are there, what is the rate of a reaction, which units does a parameter have, what is it annotated with.

`sbmlutils` produces the content of such a report as JSON. [sbml4humans.de](https://sbml4humans.de) renders it in the browser.

## The content of a model

`SBMLDocumentInfo` walks a document and collects everything about it:

```python
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo

info = SBMLDocumentInfo.from_sbml("model.xml")
print(info.to_json())
```

The result has one entry per model of the document; the elements of a model are grouped by their SBML type:

| key | content |
| --- | --- |
| `info.info["doc"]` | the document itself |
| `info.info["model"]` | the model, its units, its history and its packages |
| `info.info["modelDefinitions"]` | the comp model definitions |
| `info.info["externalModelDefinitions"]` | the external model definitions |

The elements of the model are lists under it, one per SBML type:

| key | content |
| --- | --- |
| `info.info["model"]["species"]` | every species with its compartment, units and annotations |
| `info.info["model"]["reactions"]` | every reaction with its equation, its rate and its modifiers |
| `info.info["model"]["parameters"]` | every parameter with its value and its unit |
| `info.info["model"]["compartments"]`, `["rules"]`, `["events"]`, ... | the remaining types |

Every element carries a primary key (`pk`) which identifies it across the document, so the report can link from a reaction to the species it consumes.

Every element carries what it means, not only what it says: the equation of a reaction as a readable string, the math as latex, the unit as `mmol/min/l` instead of a chain of unit elements, and the annotations with their qualifier and resource.

`to_json(strip=True)`, the default, removes the empty entries, which is what makes the result readable.

## Math as latex

The math of a model is rendered as latex, which is what the report displays:

```python
from sbmlutils.report.mathml import formula_to_latex

formula_to_latex("Vmax * glc / (Km + glc)")
# ' \\frac{\\mathit{Vmax}·\\mathit{glc}}{\\mathit{Km}+\\mathit{glc}}'
```

`astnode_to_latex` does the same for a libsbml `ASTNode`, `cmathml_to_latex` for content MathML, and `formula_to_astnode` parses a formula into an `ASTNode`.

## Units as a string

`udef_to_string` renders a unit definition, see [Units](units.md#rendering-a-unit):

```python
from sbmlutils.report.units import udef_to_string

udef_to_string(udef, format="str")  # 'mmol/min/l'
udef_to_string(udef, format="latex")  # '\\frac{mmol}{min \\cdot l}'
```

## A report in the browser

`create_online_report` serves the model on a local port, opens it on [sbml4humans.de](https://sbml4humans.de) and shuts the server down afterwards:

```python
from pathlib import Path

from sbmlutils.report.sbmlreport import create_online_report

create_online_report(sbml_path=Path("model.xml"))
```

The model is served from your machine for the duration of `fileserver_duration` (10 seconds by default) so that the site can fetch it; nothing is uploaded permanently. `server="localhost:3456"` points it at a local instance of the frontend.

The frontend and the http api behind sbml4humans.de live in [matthiaskoenig/sbml4humans](https://github.com/matthiaskoenig/sbml4humans); the report itself, i.e. `SBMLDocumentInfo`, is part of sbmlutils and is what that api serves.
