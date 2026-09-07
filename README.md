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
- **converters** — SBML to an ODE system (python, R, julia, markdown, latex), XPP to SBML, antimony in both directions

The documentation is available at [https://matthiaskoenig.github.io/sbmlutils](https://matthiaskoenig.github.io/sbmlutils).

If you have any questions or issues please [open an issue](https://github.com/matthiaskoenig/sbmlutils/issues).


## How to cite
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.597149.svg)](https://doi.org/10.5281/zenodo.597149)

If you use `sbmlutils` please cite the archived software on [Zenodo](https://doi.org/10.5281/zenodo.597149):

> König, M. (2026). *sbmlutils: Python utilities for SBML* (Version 0.9.6) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.18207772

```bibtex
@software{konig_sbmlutils,
  author    = {König, Matthias},
  title     = {sbmlutils: Python utilities for SBML},
  year      = {2026},
  month     = jan,
  version   = {0.9.6},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.18207772},
  url       = {https://doi.org/10.5281/zenodo.18207772},
}
```

## License
- Source Code: [MIT](https://opensource.org/license/MIT)
- Documentation: [CC BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/)

## Funding
Matthias König is supported by the German Research Foundation (DFG) within the Research Unit Programme FOR 5151 "QuaLiPerF (Quantifying Liver Perfusion-Function Relationship in Complex Resection - A Systems Medicine Approach)" by grant number 436883643 and by grant number 465194077 (Priority Programme SPP 2311, Subproject SimLivA).

Matthias König was supported by the Federal Ministry of Education and Research (BMBF, Germany) within the research network Systems Medicine of the Liver (**LiSyM**, grant number 031L0054). Matthias König has received funding from the EOSCsecretariat.eu which has received funding from the European Union's Horizon Programme call H2020-INFRAEOSC-05-2018-2019, grant Agreement number 831644.

© 2017-2026 Matthias König, [https://livermetabolism.com](https://livermetabolism.com)
