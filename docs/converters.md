# Converters

The converters import models from other formats and recover a Python model definition from SBML. Deriving differential equations and exporting simulation code or equation documents is covered in [ODE export](ode.md).

## XPP to SBML

[XPP/XPPAUT](http://www.math.pitt.edu/~bard/xpp/xpp.html) models are `.ode` files. `xpp2sbml` converts one to SBML:

```python
from pathlib import Path

from sbmlutils.converters import xpp

xpp.xpp2sbml(xpp_file=Path("model.ode"), sbml_file=Path("model.xml"))
```

The parameters, initial conditions, ODEs, auxiliary variables, functions, markov chains and global (event) statements of the ode file become the corresponding SBML elements. `force_lower=True` lowercases the identifiers, which some ode files rely on.

All three packaged ode files (`PLoSCompBiol_Fig1`, `112836_HH-ext` and `SkM_AP_KCa`, in `sbmlutils/resources/testdata/xpp/`) convert to models which validate without an error or a warning; `tests/converters/test_xpp.py` checks this. Two of them do not integrate with the default solver of roadrunner, which is a property of those stiff Hodgkin-Huxley models and their initial conditions, not of the conversion.

`examples/converters/xpp.py` converts a packaged ode file and simulates the result:

```bash
python -m examples.converters.xpp
```

## Antimony

[Antimony](https://tellurium.readthedocs.io/en/latest/antimony.html) is a compact text notation for models, see [Reading and writing](io.md#antimony):

```python
from sbmlutils.parser import antimony_to_model, antimony_to_sbml

sbml_str = antimony_to_sbml("J0: S1 -> S2; k1*S1; S1 = 10; S2 = 0; k1 = 0.1")
model = antimony_to_model("model.ant")
```

`sbml_to_antimony` in `sbmlutils.io` converts an SBML file or string back to antimony. `create_model` writes the antimony and the markdown of the ODE system next to the SBML file with `create_antimony=True` and `create_markdown=True`, see [Model creation](creation.md).

## Model definition from SBML

`sbml_to_model` reads an SBML file back into the `Model` object of the [model creation](creation.md), which is the converter towards sbmlutils itself:

```python
from sbmlutils.parser import sbml_to_model

model = sbml_to_model("model.xml")
```
