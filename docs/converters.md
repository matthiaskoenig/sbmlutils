# Converters

An SBML model is a description, not a program. The converters turn it into something else: the ODE system as code, a model from another format, or a file another tool understands.

## SBML to an ODE system

`SBML2ODE` derives the ordinary differential equations of a model and writes them as code:

```python
from pathlib import Path

from sbmlutils.converters.odefac import SBML2ODE

factory = SBML2ODE.from_file(sbml_file=Path("model.xml"))

factory.to_python(py_file=Path("model.py"))
factory.to_R(r_file=Path("model.R"))
factory.to_julia(jl_file=Path("model.jl"))
factory.to_markdown(md_file=Path("model.md"))
factory.to_tex(tex_file=Path("model.tex"))
```

Every method returns the generated code as a string as well, so the file argument is optional.

The generated python is a self contained module with the identifiers, the initial conditions, the parameters and the right hand side, ready for an integrator such as `scipy.integrate.odeint`:

```python
def f_dxdt(x: np.ndarray, t: float, p: np.ndarray) -> np.ndarray:
    """Right hand side of the ODE system."""
    ...


def f_y(x: np.ndarray, t: float, p: np.ndarray) -> np.ndarray:
    """Assignment rules of the model."""
    ...
```

The markdown and latex output are the equations for a paper or a model description: the state variables, the assignments and the ODEs, with the units.

The conversion resolves the assignment rules in dependency order, which is why an assignment which depends on another one comes out in the right place.

The templates behind the generation are in `sbmlutils/resources/converters/`; `to_custom_template` renders the same model through a template of your own.

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

## COPASI

COPASI displays the name of an element, not its id, which makes a model whose elements have no names unreadable in it. `write_ids_to_names` copies the ids into the names:

```python
from pathlib import Path

from sbmlutils.converters.copasi import write_ids_to_names

write_ids_to_names(input_path=Path("model.xml"), output_path=Path("model_copasi.xml"))
```

## Model definition from SBML

`sbml_to_model` reads an SBML file back into the `Model` object of the [model creation](creation.md), which is the converter towards sbmlutils itself:

```python
from sbmlutils.parser import sbml_to_model

model = sbml_to_model("model.xml")
```
