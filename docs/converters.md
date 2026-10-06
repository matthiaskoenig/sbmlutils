# Converters

An SBML model is a description, not a program. The converters turn it into something else: the ODE system as code or as a document, a model from another format, or a file another tool understands.

## SBML to an ODE system

The package [sbmlode](https://matthiaskoenig.github.io/sbmlode/), which `sbmlutils.converters.ode` re-exports, writes the system of ordinary differential equations of a model as code which simulates it, in python, julia and R, and as a document which describes it, in typst, LaTeX and markdown:

```python
from sbmlode import OdeSystem

system = OdeSystem.from_sbml("model.xml")
system.write("model.py")
system.write("model.typ")
```

The numerical code reproduces libroadrunner over the SBML test suite, events included. See [ODE export](ode.md) and the [documentation of sbmlode](https://matthiaskoenig.github.io/sbmlode/) for the formats, their options, the supported SBML and how to run the code.

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
