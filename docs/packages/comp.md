# Hierarchical Model Composition (comp)

Use comp to package a reusable model as a definition and instantiate it as a submodel. A port exposes an element of that definition so the parent model can connect to it without depending on the element's internal identifier.

## Override a rate constant in the parent model

The model definition contains a degradation reaction and exposes its rate constant through a port. The parent supplies an experimentally measured rate through that port. Flattening applies the replacement and rewrites the reaction to refer to the parent's parameter.

```python
from pathlib import Path

import libsbml

from sbmlutils.comp import flatten_sbml
from sbmlutils.factory import (
    PORT_SUFFIX,
    Compartment,
    Model,
    ModelDefinition,
    ModelUnits,
    Package,
    Parameter,
    Reaction,
    ReplacedElement,
    Species,
    Submodel,
    UnitDefinition,
    Units,
    create_model,
)


class U(Units):
    """Units shared by both models."""

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
    parameters=[Parameter("k", value=0.1, unit=U.per_second, port=True)],
    reactions=[Reaction("decay", equation="S ->", formula="k * S")],
)
experiment = Model(
    sid="experiment",
    packages=[Package.COMP_V1],
    units=U,
    model_units=model_units,
    model_definitions=[degradation],
    submodels=[Submodel("sample", modelRef="degradation")],
    parameters=[Parameter("measured_k", value=0.2, unit=U.per_second)],
    replaced_elements=[
        ReplacedElement(
            elementRef="measured_k", submodelRef="sample", portRef=f"k{PORT_SUFFIX}"
        )
    ],
)
result = create_model(experiment, Path("experiment.xml"), raise_on_error=True)
flat_doc = flatten_sbml(
    result.sbml_path, Path("experiment_flat.xml"), leave_ports=False
)

flat_model = flat_doc.getModel()
assert flat_model.getNumParameters() == 1
assert flat_model.getParameter("measured_k").getValue() == 0.2
rate = flat_model.getReaction(0).getKineticLaw().getMath()
assert "measured_k" in libsbml.formulaToL3String(rate)
```

Here the model definition is embedded in the same document. For definitions stored in separate files, use `ExternalModelDefinition`. Relative sources are resolved from the file containing the reference.

See [Model composition](../comp.md) for external definitions, replacements, deletions and nested references.
