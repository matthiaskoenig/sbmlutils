![sbmlutils logo](https://github.com/matthiaskoenig/sbmlutils/raw/develop/docs/images/sbmlutils-logo-60.png)

# sbmlutils: python utilities for SBML
[![GitHub Actions CI/CD Status](https://github.com/matthiaskoenig/sbmlutils/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/matthiaskoenig/sbmlutils/actions/workflows/ci-cd.yml)
[![Documentation](https://img.shields.io/badge/docs-sbmlutils-008080.svg)](https://matthiaskoenig.github.io/sbmlutils)
[![Version](https://img.shields.io/pypi/v/sbmlutils.svg)](https://pypi.org/project/sbmlutils/)
[![Python Versions](https://img.shields.io/pypi/pyversions/sbmlutils.svg)](https://pypi.org/project/sbmlutils/)
[![MIT License](https://img.shields.io/pypi/l/sbmlutils.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.597149.svg)](https://doi.org/10.5281/zenodo.597149)

`sbmlutils` is a collection of python utilities for working with models in the [Systems Biology Markup Language](https://sbml.org) (SBML), built on [libsbml](https://sbml.org/software/libsbml/).

Features include

- **model creation** — a model is a python object, `create_model` writes it as validated SBML, with support for the `comp`, `fbc`, `distrib` and `layout` packages
- **units** written as strings (`mmole/min/l`) and checked for consistency
- **annotations** — MIRIAM annotations and SBO terms, in the model definition or from an annotation spreadsheet
- **notes** written as markdown
- **model composition** — hierarchical models, merging and flattening
- **reports** — the complete content of a model as JSON, the basis of [sbml4humans.de](https://sbml4humans.de)
- **converters** — SBML to an ODE system (python, R, julia, markdown, latex), XPP to SBML, antimony in both directions

The documentation is available at [https://matthiaskoenig.github.io/sbmlutils](https://matthiaskoenig.github.io/sbmlutils).

If you have any questions or issues please [open an issue](https://github.com/matthiaskoenig/sbmlutils/issues).

## Installation

`sbmlutils` requires python >= 3.11 and is available from [pypi](https://pypi.python.org/pypi/sbmlutils):

```bash
pip install sbmlutils
```

The latest development version is installed with

```bash
pip install git+https://github.com/matthiaskoenig/sbmlutils.git@develop
```

See [Installation](https://matthiaskoenig.github.io/sbmlutils/installation/) for the details and [Development](https://matthiaskoenig.github.io/sbmlutils/development/) for a development setup.

## Agent facing documentation

The documentation is available as markdown for agents and language models: [llms.txt](https://matthiaskoenig.github.io/sbmlutils/llms.txt) is an annotated index of all pages, [llms-full.txt](https://matthiaskoenig.github.io/sbmlutils/llms-full.txt) is the complete documentation in a single file, and every page is served as markdown next to its html. [CLAUDE.md](CLAUDE.md) describes the repository itself.

## How to cite
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.597149.svg)](https://doi.org/10.5281/zenodo.597149)

## License
- Source Code: [MIT](https://opensource.org/license/MIT)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

## Funding
Matthias König is supported by the German Research Foundation (DFG) within the Research Unit Programme FOR 5151
"QuaLiPerF (Quantifying Liver Perfusion-Function Relationship in Complex Resection -
A Systems Medicine Approach)" by grant number 436883643 and by grant number
465194077 (Priority Programme SPP 2311, Subproject SimLivA).

Matthias König was supported by the Federal Ministry of Education and Research (BMBF, Germany)
within the research network Systems Medicine of the Liver (**LiSyM**, grant number 031L0054).
SBML4Humans was funded as part of [Google Summer of Code 2021](https://summerofcode.withgoogle.com/).
Matthias König has received funding from the EOSCsecretariat.eu which has received funding
from the European Union's Horizon Programme call H2020-INFRAEOSC-05-2018-2019, grant Agreement number 831644.

© 2017-2026 Matthias König
