# ODE export

An SBML model describes a system of ordinary differential equations (ODEs), but it is not written as one: the equations follow from the reactions, rules, events and units of the model. The ODE export derives this system and writes it as code which simulates the model (**python**, **julia**, **R**) and as a document which describes it (**typst**, **LaTeX**, **markdown**).

The ODE export is the package [sbmlode](https://matthiaskoenig.github.io/sbmlode/), a dependency of sbmlutils since 0.15.0. `sbmlutils.converters.ode` re-exports its public API (`OdeSystem`, `FORMATS`, `Format`, `render`, `write`, `render_template`), and its submodules are importable under it as well (`sbmlutils.converters.ode.system` is `sbmlode.system`), so code written against sbmlutils 0.14 keeps working. New code imports sbmlode directly.

## Quick start

```python
from sbmlode import OdeSystem

system = OdeSystem.from_sbml("model.xml")

code: str = system.render("python")  # the code or document as a string
system.write("model.py")  # the format from the suffix of the file
system.write("model.md")  # the markdown document of the system
```

`create_model(..., create_markdown=True)` writes the markdown document of the ODE system next to the SBML file, see [Model creation](creation.md).

## Documentation of sbmlode

- [Guide](https://matthiaskoenig.github.io/sbmlode/formats/): the formats and their options, the supported SBML, the numerical and the presentation formats, custom templates and the verification against libroadrunner over the SBML test suite.
- [Typed target](https://matthiaskoenig.github.io/sbmlode/typeset/): the system typeset as data (`OdeSystem.typeset`), for an application which lays out the equations itself.
- [API reference](https://matthiaskoenig.github.io/sbmlode/api/): the classes and functions of sbmlode.
- [Migration from sbmlutils](https://matthiaskoenig.github.io/sbmlode/formats/#migration-from-sbmlutils): the imports of sbmlutils and those of sbmlode, and the migration from `odefac` of sbmlutils 0.13.
