![](images/sbmlutils-logo-small.png)

# sbmlutils: python utilities for SBML
[![GitHub Actions CI/CD Status](https://github.com/matthiaskoenig/sbmlutils/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/matthiaskoenig/sbmlutils/actions/workflows/ci-cd.yml) [![Documentation](https://img.shields.io/badge/docs-sbmlutils-008080.svg)](https://matthiaskoenig.github.io/sbmlutils) [![Version](https://img.shields.io/pypi/v/sbmlutils.svg)](https://pypi.org/project/sbmlutils/) [![Python Versions](https://img.shields.io/pypi/pyversions/sbmlutils.svg)](https://pypi.org/project/sbmlutils/) [![MIT License](https://img.shields.io/pypi/l/sbmlutils.svg)](https://opensource.org/licenses/MIT) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.597149.svg)](https://doi.org/10.5281/zenodo.597149)

`sbmlutils` is a collection of python utilities for working with models in the [Systems Biology Markup Language](https://sbml.org) (SBML), built on [libsbml](https://sbml.org/software/libsbml/). The source code is available from [https://github.com/matthiaskoenig/sbmlutils](https://github.com/matthiaskoenig/sbmlutils).

## Background

SBML is the exchange format for computational models in systems biology ([Keating *et al.* 2020](references.md#sbml), [Hucka *et al.* 2019](references.md#sbml)), and libsbml is the reference implementation for reading and writing it. Working with libsbml directly is verbose: every element is created on the model, every attribute is set through a setter, and every call returns a status code which has to be checked. A compartment with a unit and an annotation is a dozen statements.

`sbmlutils` is the layer above it. A model is written as a python object — a `Model` holding `Compartment`, `Species`, `Parameter` and `Reaction` objects — and `create_model` turns that definition into a validated SBML file. The definition is data, so it can be composed, parameterized and generated, and the units, annotations and notes belong to the element they describe instead of being applied afterwards.

Around this core the package collects the tasks which come with SBML models: validating them, merging them, flattening a hierarchical model, converting them to other formats, and describing them in a human readable report.

## Features

- **[Model creation](creation.md)** — define a model as python objects and write it as SBML with `create_model`, with support for the `comp`, `fbc`, `distrib` and `layout` packages.
- **[Units](units.md)** — units are written as strings (`mmole/min/l`), parsed with [pint](https://pint.readthedocs.io) and converted into SBML unit definitions; the model is checked for unit consistency.
- **[Annotations](annotations.md)** — MIRIAM annotations and SBO terms on every element, either in the model definition or applied to an existing model from an annotation spreadsheet.
- **[Notes](notes.md)** — element documentation written as markdown, converted to the XHTML notes SBML requires.
- **[Validation](validation.md)** — the libsbml checks with a readable report and configurable consistency options.
- **[Model composition](comp.md)** — hierarchical models with the `comp` package: submodels, ports, replacements, and flattening into a single model.
- **[Flux balance constraints](fbc.md)** — `fbc` models with flux bounds, objectives, gene products and user defined constraints, and a bridge to [cobrapy](https://cobrapy.readthedocs.io).
- **[COMBINE archives](omex.md)** — models packaged as OMEX archives through [pymetadata](https://github.com/matthiaskoenig/pymetadata).
- **[Reports](reports.md)** — the complete content of a model as JSON, the basis of the reports on [sbml4humans.de](https://sbml4humans.de).
- **[Converters](converters.md)** — SBML to an ODE system (python, R, julia, markdown, latex), XPP/XPPAUT `.ode` files to SBML, and antimony in both directions.
- **[Interpolation](interpolation.md)** — a table of data points as an SBML model, with constant, linear and cubic spline interpolation.
- **[Visualization](visualization.md)** — models rendered as a network in [Cytoscape](https://cytoscape.org).

The specifications behind the language and its packages are cited in [References](references.md).

## Quickstart

A model is a python object, `create_model` writes it as SBML:

```python
from pathlib import Path

from sbmlutils.factory import (
    Compartment,
    Model,
    ModelUnits,
    Parameter,
    Reaction,
    Species,
    UnitDefinition,
    Units,
    create_model,
)


class U(Units):
    """Units of the model."""

    min = UnitDefinition("min")
    mmole = UnitDefinition("mmole")
    litre = UnitDefinition("l", "liter")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")


model = Model(
    sid="glucose_uptake",
    name="glucose uptake",
    units=U,
    model_units=ModelUnits(
        time=U.min, substance=U.mmole, extent=U.mmole, volume=U.litre
    ),
    compartments=[Compartment("cell", value=1.0, unit=U.litre, name="cell")],
    species=[
        Species(
            "glc", initialConcentration=5.0, compartment="cell", substanceUnit=U.mmole
        ),
        Species(
            "g6p", initialConcentration=0.0, compartment="cell", substanceUnit=U.mmole
        ),
    ],
    parameters=[Parameter("Vmax", 1.0, U.mmole_per_min), Parameter("Km", 0.1, U.mM)],
    reactions=[
        Reaction(
            "GLUT",
            equation="glc -> g6p",
            formula=("Vmax * glc / (Km + glc)", U.mmole_per_min),
            name="glucose transport",
        )
    ],
)

result = create_model(model=model, filepath=Path("glucose_uptake.xml"))
```

Existing models are read, validated and described:

```python
from sbmlutils.io import read_sbml, validate_sbml
from sbmlutils.report.sbmlinfo import SBMLDocumentInfo

doc = read_sbml("glucose_uptake.xml")
validate_sbml("glucose_uptake.xml")

info = SBMLDocumentInfo.from_sbml("glucose_uptake.xml")
print(info.to_json()[:200])
```

Continue with [Installation](installation.md) and the [model creation guide](creation.md).

## How to cite

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.597149.svg)](https://doi.org/10.5281/zenodo.597149)

If you use `sbmlutils` please cite the archived software on [Zenodo](https://doi.org/10.5281/zenodo.597149):

> König, M. (2026). *sbmlutils: Python utilities for SBML* (Version 0.10.0) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.22646678

```bibtex
@software{konig_sbmlutils,
  author    = {König, Matthias},
  title     = {sbmlutils: Python utilities for SBML},
  year      = {2026},
  month     = sep,
  version   = {0.10.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.22646678},
  url       = {https://doi.org/10.5281/zenodo.22646678},
}
```

## License

- Source Code: [MIT](https://opensource.org/license/MIT)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

## Funding

Matthias König is supported by the German Research Foundation (DFG) within the Research Unit Programme FOR 5151 "QuaLiPerF (Quantifying Liver Perfusion-Function Relationship in Complex Resection — A Systems Medicine Approach)" by grant number 436883643 and by grant number 465194077 (Priority Programme SPP 2311, Subproject SimLivA).

Matthias König was supported by the Federal Ministry of Education and Research (BMBF, Germany) within the research network Systems Medicine of the Liver (**LiSyM**, grant number 031L0054). SBML4Humans was funded as part of [Google Summer of Code 2021](https://summerofcode.withgoogle.com/). Matthias König has received funding from the EOSCsecretariat.eu which has received funding from the European Union's Horizon Programme call H2020-INFRAEOSC-05-2018-2019, grant Agreement number 831644.
