"""Examples for model creation."""
from pathlib import Path
from sbmlutils.examples.dallaman import factory as dallaman_factory
from sbmlutils.examples.demo import factory as demo_factory
from sbmlutils.examples.tiny_model import factory as tiny_factory
from sbmlutils.factory import create_model

from sbmlutils.examples import (
    algebraic_rule,
    annotation,
    assignment,
    compartment_species_reaction,
    distrib_comp,
    distrib_distributions,
    distrib_uncertainties,
    fbc_example,
    fbc_mass_charge,
    linear_chain,
    minimal_model,
    minimal_model_comp,
    model_composition,
    model_definitions,
    multiple_substance_units,
    notes,
    model,
    parameter,
    random_network,
    reaction,
    reaction_with_units,
    species,
    unit_definitions,
    units_namespace,
)

examples_create = [
    distrib_comp,
    minimal_model_comp,
    model_composition,
    model_definitions,
    dallaman_factory,
    demo_factory,
    tiny_factory,
]

examples_models = [
    algebraic_rule,
    annotation,
    assignment,
    compartment_species_reaction,
    distrib_distributions,
    distrib_uncertainties,
    fbc_example,
    fbc_mass_charge,
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


if __name__ == "__main__":
    from sbmlutils.resources import EXAMPLES_DIR

    # for module in examples_models:
    #     model = module.model
    #
    #     model_path: Path = EXAMPLES_DIR / f"{model.sid}.xml"
    #     create_model(
    #         model=module.model,
    #         filepath=model_path,
    #     )
    #     assert model_path.exists()

    for module in examples_create:
        print(module)
        module.create(tmp=False)


