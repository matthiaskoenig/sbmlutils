# Migration

The cleanup on the development branch removes the COBRApy integration, data interpolation, the Cytoscape integration, the COPASI helper and the query of the curated BioModels from sbmlutils. The ODE import path now emits a deprecation warning.

## COBRA integration

The `cobra` extra and `sbmlutils.fbc.cobra` module have been removed. Install [COBRApy](https://cobrapy.readthedocs.io/) separately in applications that solve flux balance problems and use its API directly:

```bash
pip install cobra
```

```python
from cobra.io import read_sbml_model

model = read_sbml_model("fbc_model.xml")
solution = model.optimize()
print(solution.objective_value)

for reaction in model.reactions:
    print(reaction.id, reaction.bounds, reaction.objective_coefficient)
    print(reaction.check_mass_balance())
```

`cobra.io.read_sbml_model` replaces `read_cobra_model`. The reaction properties replace `cobra_reaction_info`, and `Reaction.check_mass_balance()` replaces the sbmlutils mass balance wrapper. These operations need an appropriate constraint based model and, for optimization, a solver supported by COBRApy. This example runs in the separate COBRApy environment, not the sbmlutils development environment.

Creating and validating fbc models does not require COBRApy. Continue using the [fbc factory objects](packages/fbc.md) and `sbmlutils.fbc.fbc.add_default_flux_bounds`.

## Interpolation

The `sbmlutils.data` package, including `sbmlutils.data.interpolation.Interpolation`, `Interpolator`, the interpolation methods and the driving helpers, has been removed. The interpolation examples and their packaged data and generated models have also been removed.

Interpolating measured data to drive a simulation now lives in [`sbmlsim.interpolation`](https://matthiaskoenig.github.io/sbmlsim/interpolation/). Install a version of sbmlsim that includes the migration, then update the imports:

```python
# Before
from sbmlutils.data.interpolation import Interpolation, InterpolationMethod

# After
from sbmlsim.interpolation import Interpolation, InterpolationMethod
```

`Interpolator` and the `INTERPOLATION_CONSTANT`, `INTERPOLATION_LINEAR` and `INTERPOLATION_CUBIC_SPLINE` aliases are also available from `sbmlsim.interpolation`. The `drive`, `drive_comp`, `assignment_rules` and standalone interpolation model writers retain their behavior. See the [sbmlsim guide](https://matthiaskoenig.github.io/sbmlsim/interpolation/) for complete examples.

Existing SBML files containing interpolated assignment rules remain ordinary SBML. They can still be [read, written](io.md) and [validated](validation.md) without the interpolation API.

## Cytoscape

The `cytoscape` extra and the `sbmlutils.cytoscape` module (`visualize_sbml`, `visualize_antimony`, `apply_layout`, `add_annotations`, `export_image` and the annotation shapes) have been removed. Load an SBML file in [Cytoscape](https://cytoscape.org/) with the [cy3sbml](https://apps.cytoscape.org/apps/cy3sbml) app, or drive a running Cytoscape with [py4cytoscape](https://py4cytoscape.readthedocs.io/) directly. Positions which belong to the model are stored with the [layout package](visualization.md).

## COPASI helper

`sbmlutils.converters.copasi.write_ids_to_names` has been removed. It replaced the names of the elements by their ids for the display in COPASI; set the names in the model definition instead.

## Curated BioModels

`sbmlutils.biomodels.query_curated_biomodels` and the helper which built the test archives have moved into the repository script `scripts/biomodels.py`, see [Development](development.md#biomodels-fixtures). `download_biomodel_omex` and `download_biomodel_sbml` stay in `sbmlutils.biomodels`.

## ODE imports

Import the ODE export from `sbmlode`. The deprecated `sbmlutils.converters.ode` namespace still resolves the same API and submodules and emits a `DeprecationWarning`.

```python
from sbmlode import OdeSystem, render
from sbmlode.system import OdeSystem
```

Use the first form for public API objects, or replace the old module prefix with `sbmlode` when importing from a specific submodule. The factory option `create_model(create_markdown=True)` still writes an ODE document. See [ODE export](ode.md) for usage.
