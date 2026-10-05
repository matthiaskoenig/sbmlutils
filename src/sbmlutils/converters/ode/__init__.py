"""Export of an SBML model as its system of ordinary differential equations.

`OdeSystem.from_sbml` analyses a model into its ODE system, which is rendered in the
formats of `FORMATS`:

```python
from sbmlutils.converters.ode import OdeSystem

system = OdeSystem.from_sbml("model.xml")
code = system.render("python", simulator=True)
system.write("model.py")
```

The methods `render`, `write` and `render_template` of `OdeSystem` are the functions of
the same names of this package, which take the system as their first argument.

The math of the model is written by the printers of `sbmlutils.converters.ode.printers`,
one per dialect, the text of the model through the helpers of
`sbmlutils.converters.ode.text`, the formats by `sbmlutils.converters.ode.formats`:
python, julia and R code, and typst, LaTeX and markdown documents
(`sbmlutils.converters.ode.documents`), e.g. `system.write("model.typ")`.
"""

from sbmlutils.converters.ode.formats import (
    FORMATS,
    Format,
    render,
    render_template,
    write,
)
from sbmlutils.converters.ode.system import OdeSystem

__all__: list[str] = [
    "FORMATS",
    "Format",
    "OdeSystem",
    "render",
    "render_template",
    "write",
]
