# Model composition

Large models are built from smaller ones. The SBML [comp](https://sbml.org/documents/specifications/level-3/version-1/comp/) package makes this explicit: a model includes other models as *submodels*, exposes elements through *ports*, and connects them by *replacing* an element of a submodel with one of the parent model.

## Ports

A port is the interface of a model — the elements another model is allowed to connect to. Any element is exported by setting `port=True`:

```python
from sbmlutils.factory import Compartment, Model, Package, Species

model = Model(
    sid="cell",
    packages=[Package.COMP_V1],
    compartments=[Compartment("cell", value=1.0, port=True)],
    species=[Species("S1", initialConcentration=10.0, compartment="cell", port=True)],
)
```

The port of an element gets the id of the element plus `PORT_SUFFIX` (`_port`), so the port of `cell` is `cell_port`. A unit port uses `PORT_UNIT_SUFFIX` (`_unit_port`). A `Port` object is created explicitly when the id or the reference has to be different.

## Submodels

A submodel refers to a model definition, which is either inside the same file (`ModelDefinition`) or in another file (`ExternalModelDefinition`):

```python
from sbmlutils.factory import ExternalModelDefinition, Submodel

model.external_model_definitions = [
    ExternalModelDefinition(sid="emd0", source="cell.xml", modelRef="cell"),
]
model.submodels = [Submodel(sid="submodel0", modelRef="emd0")]
```

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

`ReplacedBy` is the other direction — an element of this model is replaced *by* one of a submodel — and `Deletion` removes an element of a submodel.

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
