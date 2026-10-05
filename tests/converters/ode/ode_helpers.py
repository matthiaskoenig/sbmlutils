"""Helpers shared by the tests of the ODE export.

The helpers are imported as `from ode_helpers import ...`: pytest puts the directory
of a test module on `sys.path` (prepend import mode, no `__init__.py`).
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import libsbml


def sbml_with_rate(formula: str, name: str = "species A", sid: str = "A") -> str:
    """SBML of a model with one species which is consumed by one reaction.

    The model holds the compartment `c` (size 2), the parameter `k` (0.5), the
    species `sid` (initial concentration 3) and the reaction `v` with the rate law
    `formula`.

    Args:
        formula: rate law of the reaction, an L3 infix formula
        name: name of the species, the compartment, the parameter and the reaction,
            in XML syntax, so that a character reference is written as it is
        sid: id of the species

    Returns:
        the SBML string
    """
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    model.setId("m")
    c: libsbml.Compartment = model.createCompartment()
    c.setId("c")
    c.setName("NAME")
    c.setSize(2.0)
    c.setConstant(True)
    k: libsbml.Parameter = model.createParameter()
    k.setId("k")
    k.setName("NAME")
    k.setValue(0.5)
    k.setConstant(True)
    s: libsbml.Species = model.createSpecies()
    s.setId(sid)
    s.setName("NAME")
    s.setCompartment("c")
    s.setInitialConcentration(3.0)
    s.setHasOnlySubstanceUnits(False)
    s.setBoundaryCondition(False)
    s.setConstant(False)
    r: libsbml.Reaction = model.createReaction()
    r.setId("v")
    r.setName("NAME")
    r.setReversible(False)
    reactant: libsbml.SpeciesReference = r.createReactant()
    reactant.setSpecies(sid)
    reactant.setStoichiometry(1.0)
    reactant.setConstant(True)
    law: libsbml.KineticLaw = r.createKineticLaw()
    math = libsbml.parseL3Formula(formula)
    assert math is not None, libsbml.getLastParseL3Error()
    law.setMath(math)
    sbml = str(libsbml.writeSBMLToString(doc))
    return sbml.replace('name="NAME"', f'name="{name}"')


def import_module(path: Path) -> ModuleType:
    """Import the python module written to the given path.

    Args:
        path: path of the python file, its stem is the name of the module

    Returns:
        the imported module
    """
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
