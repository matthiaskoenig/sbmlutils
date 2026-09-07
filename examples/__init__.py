"""Examples for model creation."""

from pathlib import Path

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
    # for module in examples_models:
    #     model = module.model
    #
    #     model_path: Path = Path.cwd() / f"{model.sid}.xml"
    #     create_model(
    #         model=module.model,
    #         filepath=model_path,
    #     )
    #     assert model_path.exists()

    import tempfile

    with tempfile.TemporaryDirectory() as tmp_dir:
        for module in examples_create:
            print(module)

            module.create(output_dir=Path(tmp_dir))
