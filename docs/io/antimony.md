# Antimony

[Antimony](https://tellurium.readthedocs.io/en/latest/antimony.html) is a compact text notation for models. `sbmlutils.parser` reads it as SBML or as a Python model definition.

## Reading

```python
from sbmlutils.parser import antimony_to_model, antimony_to_sbml

source = """
model example
    J0: S1 -> S2; k1*S1
    S1 = 10; S2 = 0; k1 = 0.1
end
"""
sbml_str = antimony_to_sbml(source)
model = antimony_to_model(source)
```

Both functions accept Antimony as a string or as a path to an `.ant` file.

## Writing

`sbml_to_antimony` in `sbmlutils.io` accepts an SBML string or the path to an SBML file:

```python
from sbmlutils.io import sbml_to_antimony

ant_str = sbml_to_antimony(sbml_str)
```

`create_model` writes Antimony next to the SBML file with `create_antimony=True`. See [Model creation](../creation.md) for the available output options and [Reading and writing](../io.md) for SBML files and strings.
