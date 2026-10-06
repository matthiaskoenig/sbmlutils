"""Export of an SBML model as its system of ordinary differential equations.

The ODE export is the package [sbmlode](https://matthiaskoenig.github.io/sbmlode/),
which this module re-exports, so code written against `sbmlutils.converters.ode`
keeps working:

```python
from sbmlutils.converters.ode import OdeSystem

system = OdeSystem.from_sbml("model.xml")
code = system.render("python", simulator=True)
system.write("model.md")
```

The submodules of sbmlode are importable under this module as well:
`sbmlutils.converters.ode.system` is the module `sbmlode.system`, the same object,
and so on for every module of sbmlode, e.g. `sbmlutils.converters.ode.printers.latex`.
They exist at runtime only, a type checker does not see them: new code imports
sbmlode directly. The guide, the formats and the API reference are
in the documentation of sbmlode, https://matthiaskoenig.github.io/sbmlode/.
"""

import importlib
import pkgutil
import sys

import sbmlode
from sbmlode import FORMATS, Format, OdeSystem, render, render_template, write

__all__: list[str] = [
    "FORMATS",
    "Format",
    "OdeSystem",
    "render",
    "render_template",
    "write",
]


def _alias_submodules() -> None:
    """Make every module of sbmlode importable under the name of this module.

    `sbmlutils.converters.ode.<name>` is registered in `sys.modules` as the module
    `sbmlode.<name>`, so `import sbmlutils.converters.ode.system` and
    `from sbmlutils.converters.ode.system import OdeSystem` give the objects of
    sbmlode, not copies of them.
    """
    for info in pkgutil.walk_packages(sbmlode.__path__, prefix="sbmlode."):
        module = importlib.import_module(info.name)
        alias = __name__ + info.name.removeprefix("sbmlode")
        sys.modules[alias] = module
        parent, _, child = alias.rpartition(".")
        setattr(sys.modules[parent], child, module)


_alias_submodules()
