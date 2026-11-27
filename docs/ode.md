# ODE export

An SBML model describes a system of ordinary differential equations (ODEs), but it is not written as one: the equations follow from the reactions, rules, events and units of the model. The ODE export derives this system and writes it as code which simulates the model (**python**, **Diffrax/JAX**, **julia**, **R**) and as a document which describes it (**typst**, **LaTeX**, **markdown**).

The ODE export uses the shared Rust generator in [sbmlsim-core](https://matthiaskoenig.github.io/sbmlsim-core/odes/). Import `OdeSystem` directly from `sbmlsim_core`.

The system uses the native quantities of the SBML state variables. A species is a state in amount or concentration as the model declares it. For a species in concentration, the ODE includes dilution when its compartment changes size.

## Quick start

```python
from sbmlsim_core import OdeSystem
from sbmlutils.resources import REPRESSILATOR_SBML

system = OdeSystem.from_sbml(REPRESSILATOR_SBML)

code: str = system.render("python")  # the code or document as a string
system.write("model.py")  # the format from the suffix of the file
system.write("model.typ")  # the Typst document of the system
system.write("model.md")  # the markdown document of the system
```

The example uses the repressilator model bundled with sbmlutils. Pass original XML bytes or a trusted file path for another model. `system.write("model_jax.py", fmt="diffrax")` selects JAX explicitly because Python and Diffrax share `.py`. Mathematical analysis, comp expansion, formatting and templates run in Rust.

`create_model(..., create_markdown=True)` writes the markdown document of the ODE system next to the SBML file, see [Model creation](creation.md).

## Shared generator

See [ODE source exports](https://matthiaskoenig.github.io/sbmlsim-core/odes/) for options, companion documents, typed equations, custom templates and native/browser usage.

The deprecated `sbmlutils.converters.ode` namespace retains the public `OdeSystem`, `FORMATS`, `Format`, `render`, `write` and `render_template` spellings, with `system` and `formats` aliases. Former Python printer internals are replaced by Rust and are no longer re-exported. Import the public API from `sbmlsim_core` for new code.

The shared `typeset()` target returns JSON-compatible linked LaTeX data instead of the former Python dataclasses. Pass original bytes or the factory's written file path; live libSBML document objects and Python printer callbacks are replaced by the Rust source API.
