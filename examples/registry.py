"""Registry of the examples which the tests build and run.

The lists live here and not in `examples/__init__.py`, because importing the
package `examples` would import every example, and `python -m examples.X` would
then find `examples.X` in `sys.modules` before running it.
"""

from examples import (
    algebraic_rule,
    annotation,
    assignment,
    compartment_species_reaction,
    model,
    model_definitions,
    multiple_substance_units,
    notes,
    parameter,
    reaction,
    reaction_with_units,
    species,
    unit_definitions,
    units_namespace,
)
from examples.dallaman import dallaman
from examples.demo import demo
from examples.distrib import (
    distrib_comp,
    distrib_distributions,
    distrib_uncertainties,
)
from examples.fbc import (
    fbc_mass_charge,
    fbc_userdefinedconstraints,
    fbc_v2,
    fbc_v3,
)
from examples.tiny import tiny
from examples.tutorial import (
    linear_chain,
    minimal_model,
    minimal_model_comp,
    model_composition,
    random_network,
)

examples_create = [
    distrib_comp,
    minimal_model_comp,
    model_composition,
    dallaman,
    demo,
    tiny,
]

examples_models = [
    algebraic_rule,
    annotation,
    assignment,
    compartment_species_reaction,
    distrib_distributions,
    distrib_uncertainties,
    fbc_v2,
    fbc_v3,
    fbc_mass_charge,
    fbc_userdefinedconstraints,
    linear_chain,
    minimal_model,
    model,
    model_definitions,
    multiple_substance_units,
    notes,
    parameter,
    random_network,
    reaction,
    reaction_with_units,
    species,
    unit_definitions,
    units_namespace,
]
