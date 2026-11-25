# ODE export

An SBML model describes a system of ordinary differential equations (ODEs), but it is not written as one: the equations follow from the reactions, rules, events and units of the model. The ODE export derives this system and writes it as code which simulates the model (**python**, **julia**, **R**) and as a document which describes it (**typst**, **LaTeX**, **markdown**).

The ODE export uses [sbmlode](https://matthiaskoenig.github.io/sbmlode/), a dependency of sbmlutils since 0.15.0. Import the API and submodules directly from `sbmlode`. The legacy `sbmlutils.converters.ode` namespace remains available for compatibility and emits a `DeprecationWarning` on import. See [Migration](migration.md#ode-imports) for the import changes.

sbmlutils requires sbmlode 0.3.3 or later, which writes the system in the native quantities of the SBML state variables: a species is a state in amount or in concentration as the model declares it, also in a compartment whose size changes, where the ODE of a species in concentration carries the dilution by the rate of the size. The system is never rewritten in the amounts of the species, so the `amounts` of the system and of its documents, which sbmlode 0.1.0 wrote, are gone; see the [release notes of sbmlode 0.2.0](https://github.com/matthiaskoenig/sbmlode/blob/develop/release-notes/0.2.0.md).

## Quick start

```python
from sbmlode import OdeSystem
from sbmlutils.resources import REPRESSILATOR_SBML

system = OdeSystem.from_sbml(REPRESSILATOR_SBML)

code: str = system.render("python")  # the code or document as a string
system.write("model.py")  # the format from the suffix of the file
system.write("model.typ")  # the Typst document of the system
system.write("model.md")  # the markdown document of the system
```

The example uses the repressilator model bundled with sbmlutils. Pass the path of your own SBML file to export another model. The numerical code reproduces libroadrunner over the SBML test suite, including events; see the [verification in sbmlode](https://matthiaskoenig.github.io/sbmlode/formats/) for the supported SBML and test coverage.

`create_model(..., create_markdown=True)` writes the markdown document of the ODE system next to the SBML file, see [Model creation](creation.md).

## Documentation of sbmlode

- [Guide](https://matthiaskoenig.github.io/sbmlode/formats/): the formats and their options, the supported SBML, the numerical and the presentation formats, custom templates and the verification against libroadrunner over the SBML test suite.
- [Typed target](https://matthiaskoenig.github.io/sbmlode/typeset/): the system typeset as data (`OdeSystem.typeset`), for an application which lays out the equations itself.
- [API reference](https://matthiaskoenig.github.io/sbmlode/api/): the classes and functions of sbmlode.
- [Migration from sbmlutils](https://matthiaskoenig.github.io/sbmlode/formats/#migration-from-sbmlutils): the imports of sbmlutils and those of sbmlode, and the migration from `odefac` of sbmlutils 0.13.
