# XPP

[XPP/XPPAUT](http://www.math.pitt.edu/~bard/xpp/xpp.html) models are `.ode` files. `xpp2sbml` imports one as SBML:

```python
from pathlib import Path

from sbmlutils.converters import xpp

xpp.xpp2sbml(xpp_file=Path("model.ode"), sbml_file=Path("model.xml"))
```

The parameters, initial conditions, ODEs, auxiliary variables, functions, Markov chains and global event statements of the `.ode` file become the corresponding SBML elements. `force_lower=True` lowercases the identifiers, which some `.ode` files rely on.

All three packaged `.ode` files (`PLoSCompBiol_Fig1`, `112836_HH-ext` and `SkM_AP_KCa`, in `sbmlutils/resources/testdata/xpp/`) produce models which validate without an error or a warning; `tests/converters/test_xpp.py` checks this. Two of them do not integrate with the default solver of roadrunner because of their stiff Hodgkin-Huxley models and initial conditions.

`examples/converters/xpp.py` imports a packaged `.ode` file and simulates the result:

```bash
python -m examples.converters.xpp
```

See [Reading and writing](../io.md) for SBML files and strings and the [XPP API](../api/converters.xpp.md) for the import options.
