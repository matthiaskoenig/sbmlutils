"""Export of an SBML model as its system of ordinary differential equations.

`OdeSystem.from_sbml` analyses a model into its ODE system, which is rendered in the
formats of `FORMATS`:

```python
from sbmlutils.converters.ode import OdeSystem

system = OdeSystem.from_sbml("model.xml")
code = system.render("python", simulator=True)
system.write("model.py")
```

The math of the model is written by the printers of `sbmlutils.converters.ode.printers`,
one per dialect, the text of the model through the helpers of
`sbmlutils.converters.ode.text`, the formats by `sbmlutils.converters.ode.formats`.
"""

from sbmlutils.converters.ode.formats import FORMATS, Format
from sbmlutils.converters.ode.system import OdeSystem

__all__: list[str] = ["FORMATS", "Format", "OdeSystem"]
