# API reference

The API reference is generated from the docstrings of the package.

## sbmlutils

The top level modules: the model definition, reading and writing, validation and the shared output.

| module | description |
| --- | --- |
| [factory](factory.md) | the model definition and `create_model`, the entry point of the package |
| [io](io.md) | reading and writing SBML |
| [validation](validation.md) | validation of a document against the SBML specification |
| [parser](parser.md) | SBML and antimony into a model definition |
| [notes](notes.md) | element documentation written as markdown |
| [reaction_equation](reaction_equation.md) | the stoichiometry of a reaction as a string |
| [biomodels](biomodels.md) | models from the BioModels database |
| [cytoscape](cytoscape.md) | models rendered as a network in Cytoscape |
| [console](console.md) | shared rich console |
| [log](log.md) | logging of the package |
| [utils](utils.md) | meta ids and the frozen base class |

## sbmlutils.comp

Hierarchical models with the comp package, see [Model composition](../comp.md).

| module | description |
| --- | --- |
| [comp.comp](comp.comp.md) | ports, external model definitions and replacements |
| [comp.flatten](comp.flatten.md) | flattening a comp model into a single model |

## sbmlutils.converters

Conversion of a model into another representation, see [Converters](../converters.md).

| module | description |
| --- | --- |
| [converters.odefac](converters.odefac.md) | the ODE system as python, R, julia, markdown or latex |
| [converters.xpp](converters.xpp.md) | XPP/XPPAUT ode files to SBML |
| [converters.copasi](converters.copasi.md) | ids written into the names for COPASI |
| [converters.mathml](converters.mathml.md) | evaluation of MathML |

## sbmlutils.data

| module | description |
| --- | --- |
| [data.interpolation](data.interpolation.md) | data points as an SBML model, see [Interpolation](../interpolation.md) |

## sbmlutils.fbc

Constraint based models, see [Flux balance constraints](../fbc.md).

| module | description |
| --- | --- |
| [fbc.fbc](fbc.fbc.md) | flux bounds and boundary conditions |
| [fbc.cobra](fbc.cobra.md) | the bridge to cobrapy, the optional `cobra` extra |

## sbmlutils.layout

| module | description |
| --- | --- |
| [layout.layout](layout.layout.md) | layout information in the model, see [Visualization](../visualization.md) |

## sbmlutils.manipulation

| module | description |
| --- | --- |
| [manipulation.merge](manipulation.merge.md) | merging models into one comp model |

## sbmlutils.metadata

Annotation of models, see [Annotations](../annotations.md). The qualifiers `BQB`, `BQM` and the ontology terms `SBO` are re-exported from [pymetadata](https://matthiaskoenig.github.io/pymetadata).

| module | description |
| --- | --- |
| [metadata.annotator](metadata.annotator.md) | annotations from a file applied to a model |
| [metadata.validator](metadata.validator.md) | validation of the annotations of a model |
| [metadata.miriam](metadata.miriam.md) | the MIRIAM qualifiers of libsbml |

## sbmlutils.report

The content of a model for a human reader, see [Reports](../reports.md).

| module | description |
| --- | --- |
| [report.sbmlinfo](report.sbmlinfo.md) | the complete content of a document as JSON |
| [report.sbmlreport](report.sbmlreport.md) | a report on sbml4humans.de |
| [report.units](report.units.md) | unit definitions rendered as a string or latex |
| [report.mathml](report.mathml.md) | math rendered as latex |
