# Model composition

Large models are built from smaller ones. The SBML [comp](https://sbml.org/documents/specifications/level-3/version-1/comp/) package makes this explicit: a model includes other models as *submodels*, exposes elements through *ports*, and connects them by *replacing* an element of a submodel with one of the parent model.

## Ports

A port is the interface of a model - the elements another model is allowed to connect to. Any element is exported by setting `port=True`:

```python
from sbmlutils.factory import Compartment, Model, Package, Species

model = Model(
    sid="cell",
    packages=[Package.COMP_V1],
    compartments=[Compartment("cell", value=1.0, port=True)],
    species=[Species("S1", initialConcentration=10.0, compartment="cell", port=True)],
)
```

A model declares the comp package when it has comp content: a `port` or a `replacedBy` on any of its elements, also on a parameter or a rule of a reaction, a submodel, a port, a replaced element, a deletion or a model definition. `Package.COMP_V1` in `packages` declares it explicitly, for a model which gets its comp content later, e.g. from `sbmlutils.comp.create_ports` on the written document.

The port of an element gets the id of the element plus `PORT_SUFFIX` (`_port`), so the port of `cell` is `cell_port`. A unit port uses `PORT_UNIT_SUFFIX` (`_unit_port`). A `Port` object is created explicitly when the id or the reference has to be different.

A port names most elements by their id (`comp:idRef`), a unit definition by `comp:unitRef`, and an initial assignment, a rule, an event assignment and a local parameter by their metaid (`comp:metaIdRef`): libsbml resolves a `comp:idRef` with `Model.getElementBySId`, which answers with none of those four. Such an element needs a `metaId` for its port, which its port is then named after; an element without one is reported and gets no port.

A kinetic law, a trigger, a priority, a delay, a constraint and a key-value pair are named by their id from SBML Level 3 Version 2 on and by their metaid below it, where an SBML document carries no id for them. `create_model` writes Level 3 Version 1 by default, so a port on one of those needs a `metaId` unless the document is written as Level 3 Version 2.

## Submodels

A submodel refers to a model definition, which is either inside the same file (`ModelDefinition`) or in another file (`ExternalModelDefinition`):

```python
from sbmlutils.factory import ExternalModelDefinition, Submodel

model.external_model_definitions = [
    ExternalModelDefinition(sid="emd0", source="cell.xml", modelRef="cell"),
]
model.submodels = [Submodel(sid="submodel0", modelRef="emd0")]
```

A `ModelDefinition` is a `Model`, so it takes everything a model takes - unit definitions, compartments, species, parameters, reactions, rules, events, its own submodels and ports, and the fbc and distrib content of the model - and all of it is written into the `<comp:modelDefinition>`:

```python
from sbmlutils.factory import (
    Compartment,
    Model,
    ModelDefinition,
    Package,
    Parameter,
    Reaction,
    Species,
    Submodel,
)

cell = ModelDefinition(
    sid="cell",
    compartments=[Compartment("c", value=1.0, port=True)],
    species=[Species("S1", compartment="c", initialConcentration=10.0, port=True)],
    parameters=[Parameter("k1", value=0.1)],
    reactions=[Reaction(sid="J0", equation="S1 ->", formula="k1 * S1")],
)

tissue = Model(
    sid="tissue",
    packages=[Package.COMP_V1],
    model_definitions=[cell],
    submodels=[Submodel(sid="cell1", modelRef="cell")],
)
```

The document declares the packages the content of a model definition needs, so a model definition with gene products or uncertainties does not have to repeat them. `packages`, `model_definitions` and `external_model_definitions` belong to the document and are refused on a model definition.

## Replacements

A replacement says that an element of the parent model *is* an element of a submodel, so the two are one element after flattening:

```python
from sbmlutils.factory import PORT_SUFFIX, ReplacedElement

model.replaced_elements = [
    ReplacedElement(
        sid="cell0_RE",
        metaId="cell0_RE",
        elementRef="cell0",  # the element of this model
        submodelRef="submodel0",  # the submodel it replaces in
        portRef=f"cell{PORT_SUFFIX}",  # the port of the submodel
    ),
]
```

`ReplacedBy` is the other direction - an element of this model is replaced *by* one of a submodel - and `Deletion` removes an element of a submodel.

A reference reaches one level deep by itself. To continue it into a submodel of the submodel it names, a `Port`, a `ReplacedElement`, a `ReplacedBy` and a `Deletion` take a nested `sBaseRef`, which is an `SbaseRef` of its own and can be nested again to any depth:

```python
from sbmlutils.factory import ReplacedElement, SbaseRef

ReplacedElement(
    sid="S1_RE",
    metaId="S1_RE",
    elementRef="S1",
    submodelRef="submodel0",  # the submodel of this model
    idRef="submodel1",  # the submodel inside it
    sBaseRef=SbaseRef(sid="inner", idRef="S1"),  # the element in there
)
```

A nested level is written as a plain `<comp:sBaseRef>`, which has only the four reference attributes, so a `Port` or a `ReplacedElement` reused as one drops what a `<comp:sBaseRef>` does not have.

## A grid of coupled cells

Because the model definition is python, a composite model is built in a loop. This couples `n_cells` copies of the same model through a transport reaction:

```python
n_cells = 5

model = Model(sid="coupled_cells", packages=[Package.COMP_V1])
model.compartments = [Compartment(sid=f"cell{k}", value=1.0) for k in range(n_cells)]
model.species = [
    Species(
        sid=f"S{k}",
        initialConcentration=10.0 if k == 0 else 0.0,
        compartment=f"cell{k}",
    )
    for k in range(n_cells)
]
model.parameters = [Parameter("D", 0.01)]
model.reactions = [
    Reaction(
        sid=f"J{k}", equation=f"S{k} <-> S{k + 1}", formula=f"D * (S{k} - S{k + 1})"
    )
    for k in range(n_cells - 1)
]

model.external_model_definitions = [
    ExternalModelDefinition(sid=f"emd{k}", source="cell.xml", modelRef="cell")
    for k in range(n_cells)
]
model.submodels = [
    Submodel(sid=f"submodel{k}", modelRef=f"emd{k}") for k in range(n_cells)
]
model.replaced_elements = [
    ReplacedElement(
        sid=f"S{k}_RE",
        metaId=f"S{k}_RE",
        elementRef=f"S{k}",
        submodelRef=f"submodel{k}",
        portRef=f"S1{PORT_SUFFIX}",
    )
    for k in range(n_cells)
]
```

The complete example is `examples/tutorial/minimal_model_comp.py`, the whole body physiological model in `examples/icg/` shows the same pattern at scale.

## Flattening

Most simulators do not read comp models. `flatten_sbml` resolves the submodels, applies the replacements and writes a single flat model:

```python
from sbmlutils.comp import flatten_sbml

flatten_sbml(sbml_path="model_comp.xml", sbml_flat_path="model_flat.xml")
```

`leave_ports=False` removes the ports from the flat model as well. `flatten_sbml_doc` does the same for a document which is already read.

External model definitions are resolved relative to the file they are referenced from, so the comp model and the models it includes stay together.

## What round trips

`sbml_to_model` reads the comp content of a document, so a hierarchical model can be read, changed in python and written back, see [Reading and writing](io.md#the-packages):

| Construct | After a round trip |
| --- | --- |
| submodels | preserved, with their time and extent conversion factors |
| deletions | preserved |
| ports | preserved |
| replaced elements and `replacedBy` | preserved, with the whole nested `sBaseRef` chain |
| model definitions | preserved, with everything inside them, core as well as fbc and distrib |
| external model definitions | preserved as the reference they are, `source`, `modelRef` and `md5` |

What the round trip does not keep:

- **An external model definition is never resolved.** The file it names is not opened and its content is not pulled into the document, which is what makes the round trip faithful; resolving is what `flatten_sbml` is for. A hierarchical model therefore has to be written next to the files it references to be simulated or fully validated. libsbml resolves a `comp:source` only against a document of the same SBML level and version, so a model whose external files are Level 3 Version 1 has to be written as Level 3 Version 1 as well, or those files have to be converted with it. `create_model` writes the level and version it is given:

```python
from pathlib import Path

from sbmlutils.factory import create_model

create_model(model=model, filepath=Path("model_comp.xml"), sbml_level=3, sbml_version=1)
```
- **`fbc:strict` on a model definition.** libsbml 5.21.2 writes the attribute twice on a `<comp:modelDefinition>`, and the file then fails to parse, so it is not written there. A document whose model definition carries fbc content keeps the validation error which says the attribute is missing, and the loss is reported once per document.
- **The core `id` and `name` of a `ReplacedElement`, a `ReplacedBy`, a `Deletion` and a nested `sBaseRef`.** They are set, and libsbml 5.21.2 does not write them into the file. The comp `comp:id` and `comp:name` of a `Port` and of a `Deletion` are written normally, and so are the metaid, the SBO term, the notes and the annotations of every one of them.

The verification uses the 123 comp cases of the [SBML test suite](https://github.com/sbmlteam/sbml-test-suite) - three of which nest an `sBaseRef`, to a depth of three - and the comp files of the repository, among them the whole-body model `icg_body.xml` with its external model definition.

## Merging models

Merging is the other way to combine models: several independent models become the submodels of one comp model, without ports or replacements.

```python
from pathlib import Path

from sbmlutils.manipulation import merge_models

model_paths = {
    "BIOMD0000000001": Path("BIOMD0000000001.xml"),
    "BIOMD0000000002": Path("BIOMD0000000002.xml"),
}
doc = merge_models(model_paths, output_dir=Path("merged"))
```

This is what `create_model` does when it is given several model definitions, see [Model creation](creation.md#several-models-at-once).
