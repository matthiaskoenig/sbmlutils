# Hierarchical Model Composition (comp)

Use the SBML [comp package](https://sbml.org/documents/specifications/level-3/version-1/comp/) to assemble a model from reusable definitions. A *model definition* describes a module. A *submodel* is one instance of that definition, and a *port* gives the parent model a stable name for an element of the module. Run the examples on this page in order.

## Define a module and expose ports

The `degradation` definition contains the amount `S` in moles, a primary decay reaction, and a background decay reaction. Each first-order rate constant has units of inverse seconds, so the kinetic laws produce moles per second. `port=True` exposes `k` under its generated name, `k_port`. The explicit `Port` exposes `S` under the public name `substrate_amount`, independently of its internal ID.

```python
from pathlib import Path

import libsbml

from sbmlutils.comp import flatten_sbml
from sbmlutils.factory import (
    PORT_SUFFIX,
    AssignmentRule,
    Compartment,
    Deletion,
    ExternalModelDefinition,
    Model,
    ModelDefinition,
    ModelUnits,
    Package,
    Parameter,
    Port,
    Reaction,
    ReplacedBy,
    ReplacedElement,
    SbaseRef,
    Species,
    Submodel,
    UnitDefinition,
    Units,
    create_model,
)
from sbmlutils.io import read_sbml
from sbmlutils.validation import validate_doc


class U(Units):
    """Units used by the reusable module and its parent."""

    per_second = UnitDefinition("per_second", "1/second")


model_units = ModelUnits(time=U.second, extent=U.mole, substance=U.mole, volume=U.litre)
degradation = ModelDefinition(
    sid="degradation",
    units=U,
    model_units=model_units,
    compartments=[Compartment("cell", value=1.0, unit=U.litre)],
    species=[
        Species("S", compartment="cell", initialAmount=1.0, hasOnlySubstanceUnits=True)
    ],
    parameters=[
        Parameter("k", value=0.1, unit=U.per_second, port=True),
        Parameter("background_k", value=0.02, unit=U.per_second),
    ],
    reactions=[
        Reaction("decay", equation="S ->", formula="k * S"),
        Reaction("background_decay", equation="S ->", formula="background_k * S"),
    ],
    ports=[Port("substrate_amount", idRef="S")],
)
```

`idRef` names an ordinary SBML ID within the referenced model. Use `unitRef` for a unit definition, `metaIdRef` for a target identified by its `metaid`, and `portRef` to refer through a port. Each reference selects one target by one of these mechanisms.

## Instantiate the module twice and flatten

`modelRef="degradation"` selects the shared definition. The instance IDs `sample` and `control` distinguish the two copies. The helpers below write and reload the hierarchical and flattened files, then validate the reloaded documents. Flattening resolves the submodels and produces one model. libSBML prefixes elements from an instance with its ID and `__`, so each copy of `S` has a distinct ID. `leave_ports=False` removes the port interface from the flat output.

```python
def experiment(sid: str) -> Model:
    """Create two instances of the shared degradation module."""
    return Model(
        sid=sid,
        packages=[Package.COMP_V1],
        units=U,
        model_units=model_units,
        model_definitions=[degradation],
        submodels=[
            Submodel("sample", modelRef="degradation"),
            Submodel("control", modelRef="degradation"),
        ],
    )


def write_and_reload(model: Model, path: Path) -> libsbml.SBMLDocument:
    """Write a hierarchical model and validate its serialized form."""
    create_model(model, path, raise_on_error=True)
    doc = read_sbml(path)
    assert not validate_doc(doc).errors
    return doc


def flatten_and_reload(path: Path) -> libsbml.SBMLDocument:
    """Flatten a hierarchy and validate its serialized form."""
    flat_path = path.with_stem(f"{path.stem}_flat")
    flatten_sbml(path, flat_path, leave_ports=False, validate=True)
    doc = read_sbml(flat_path)
    assert not validate_doc(doc).errors
    return doc


path = Path("experiment.xml")
experiment_doc = write_and_reload(experiment("experiment"), path)
comp_doc = experiment_doc.getPlugin("comp")
definition = comp_doc.getModelDefinition("degradation")
ports = definition.getPlugin("comp")
assert ports.getPort("substrate_amount").getIdRef() == "S"
assert ports.getPort(f"k{PORT_SUFFIX}").getIdRef() == "k"

flat_doc = flatten_and_reload(path)
flat_model = flat_doc.getModel()
assert flat_model.getSpecies("sample__S").getInitialAmount() == 1.0
assert flat_model.getSpecies("control__S").getInitialAmount() == 1.0
```

## Replace a submodel parameter with a parent parameter

`ReplacedElement` makes the parent's `measured_k` take the place of `k` in `sample`. `elementRef` identifies the parent element in the factory. The SBML writer puts the replacement inside that element. `submodelRef` chooses the instance and `portRef` selects the target through the module's interface. On flattening, the sample's reaction uses `measured_k`, and the control keeps its original value.

```python
model = experiment("calibrated_experiment")
model.parameters = [Parameter("measured_k", value=0.2, unit=U.per_second)]
model.replaced_elements = [
    ReplacedElement(
        elementRef="measured_k", submodelRef="sample", portRef=f"k{PORT_SUFFIX}"
    )
]
path = Path("calibrated_experiment.xml")
calibrated_doc = write_and_reload(model, path)
replacement = calibrated_doc.getModel().getParameter("measured_k").getPlugin("comp")
assert replacement.getReplacedElement(0).getSubmodelRef() == "sample"

flat_doc = flatten_and_reload(path)
flat_model = flat_doc.getModel()
assert flat_model.getParameter("measured_k").getValue() == 0.2
assert flat_model.getParameter("sample__k") is None
assert flat_model.getParameter("control__k").getValue() == 0.1
rate = flat_model.getReaction("sample__decay").getKineticLaw().getMath()
assert rate.getChild(0).getName() == "measured_k"
```

## Use a submodel parameter in place of a parent parameter

`ReplacedBy` uses the submodel element in place of the parent element. Attach it to the parent element through `replacedBy`. Here libSBML keeps the parent identifier `reference_k` when it flattens the model, and its value comes from the control's `k`. Both the parent assignment rule and the control's reaction use this parameter.

```python
model = experiment("linked_reference")
model.parameters = [
    Parameter(
        "reference_k",
        value=0.0,
        unit=U.per_second,
        replacedBy=ReplacedBy(submodelRef="control", portRef=f"k{PORT_SUFFIX}"),
    ),
    Parameter("reported_k", unit=U.per_second, constant=False),
]
model.rules = [AssignmentRule("reported_k", "reference_k", unit=U.per_second)]
path = Path("linked_reference.xml")
linked_doc = write_and_reload(model, path)
reference = linked_doc.getModel().getParameter("reference_k").getPlugin("comp")
assert reference.getReplacedBy().getSubmodelRef() == "control"

flat_doc = flatten_and_reload(path)
flat_model = flat_doc.getModel()
assert flat_model.getParameter("reference_k").getValue() == 0.1
assert flat_model.getParameter("control__k") is None
assert flat_model.getRule(0).getMath().getName() == "reference_k"
rate = flat_model.getReaction("control__decay").getKineticLaw().getMath()
assert rate.getChild(0).getName() == "reference_k"
```

## Delete a reaction from one instance

A `Deletion` removes a model element from the selected instance during composition. This deletion targets `background_decay` by its internal `idRef`, leaving the definition and the control's copy intact. Before deleting an element, check that surviving rules and reactions can still resolve their references.

```python
model = experiment("without_background")
model.deletions = [
    Deletion("skip_background", submodelRef="sample", idRef="background_decay")
]
path = Path("without_background.xml")
deleted_doc = write_and_reload(model, path)
sample = deleted_doc.getModel().getPlugin("comp").getSubmodel("sample")
assert sample.getDeletion(0).getIdRef() == "background_decay"

flat_doc = flatten_and_reload(path)
flat_model = flat_doc.getModel()
assert flat_model.getReaction("sample__background_decay") is None
assert flat_model.getReaction("control__background_decay") is not None
assert flat_model.getReaction("sample__decay") is not None
```

## Reference a definition in another file

`ExternalModelDefinition` binds an ID in the parent document to a model in another SBML file. In `ExternalModelDefinition`, `modelRef` selects `calibration` inside the external file. In `Submodel`, `modelRef` selects `external_calibration` in the parent document. A relative `source` is resolved against the directory of the parent file. Keep the files in that relative arrangement when moving the model.

```python
module_path = Path("modules/calibration.xml")
module_path.parent.mkdir(exist_ok=True)
calibration = Model(
    sid="calibration",
    units=U,
    model_units=model_units,
    parameters=[Parameter("k", value=0.15, unit=U.per_second)],
)
calibration_doc = write_and_reload(calibration, module_path)

model = Model(
    sid="external_experiment",
    packages=[Package.COMP_V1],
    units=U,
    model_units=model_units,
    external_model_definitions=[
        ExternalModelDefinition(
            "external_calibration",
            source=module_path.as_posix(),
            modelRef="calibration",
        )
    ],
    submodels=[Submodel("device", modelRef="external_calibration")],
)
path = Path("external_experiment.xml")
external_doc = write_and_reload(model, path)
external = external_doc.getPlugin("comp").getExternalModelDefinition(
    "external_calibration"
)
assert external.getSource() == "modules/calibration.xml"
assert external.getModelRef() == "calibration"

flat_doc = flatten_and_reload(path)
assert flat_doc.getModel().getParameter("device__k").getValue() == 0.15
```

## Follow a nested reference

A nested `SbaseRef` continues a reference into another submodel. This replacement starts at the top-level instance `outer`, selects its child instance `inner` with `idRef`, and follows `k_port` inside `inner`. The flattened reaction has both instance prefixes and uses `measured_k` from the top level.

```python
wrapper = ModelDefinition(
    sid="wrapper",
    units=U,
    model_units=model_units,
    submodels=[Submodel("inner", modelRef="degradation")],
)
model = Model(
    sid="nested_experiment",
    packages=[Package.COMP_V1],
    units=U,
    model_units=model_units,
    model_definitions=[degradation, wrapper],
    submodels=[Submodel("outer", modelRef="wrapper")],
    parameters=[Parameter("measured_k", value=0.2, unit=U.per_second)],
    replaced_elements=[
        ReplacedElement(
            elementRef="measured_k",
            submodelRef="outer",
            idRef="inner",
            sBaseRef=SbaseRef(portRef=f"k{PORT_SUFFIX}"),
        )
    ],
)
path = Path("nested_experiment.xml")
nested_doc = write_and_reload(model, path)
replacement = nested_doc.getModel().getParameter("measured_k").getPlugin("comp")
assert replacement.getReplacedElement(0).getSBaseRef().getPortRef() == f"k{PORT_SUFFIX}"

flat_doc = flatten_and_reload(path)
rate = flat_doc.getModel().getReaction("outer__inner__decay").getKineticLaw().getMath()
assert rate.getChild(0).getName() == "measured_k"
```

## Use consistent units across modules

These models share time and extent units. When units differ, `Submodel.timeConversionFactor` and `Submodel.extentConversionFactor` can name constant parameters in the parent model. The time factor scales a submodel duration into parent time units. For a submodel in seconds and parent in minutes, the value is `1/60` minute per second. The extent factor scales a submodel reaction extent into parent extent units. Flattening scales a submodel's kinetic laws by its extent factor divided by its time factor. For more detail, see [Model composition](../comp.md) and the [comp specification](https://sbml.org/documents/specifications/level-3/version-1/comp/).
