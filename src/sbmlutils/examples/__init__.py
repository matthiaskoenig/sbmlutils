"""Examples for model creation."""
from pathlib import Path
from sbmlutils.examples.dallaman import dallaman
from sbmlutils.examples.demo import demo
from sbmlutils.examples.tiny import tiny

from sbmlutils.examples import (
    algebraic_rule,
    annotation,
    assignment,
    compartment_species_reaction,
    model_definitions,
    multiple_substance_units,
    notes,
    model,
    parameter,
    reaction,
    reaction_with_units,
    species,
    unit_definitions,
    units_namespace,
)
from sbmlutils.examples.distrib import (
    distrib_comp,
    distrib_distributions,
    distrib_uncertainties,
)

from sbmlutils.examples.tutorial import (
    linear_chain,
    minimal_model,
    minimal_model_comp,
    random_network,
    model_composition,
)
from sbmlutils.examples.fbc import (
    fbc_v2,
    fbc_v3,
    fbc_mass_charge,
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
    #     model_path: Path = EXAMPLES_DIR / f"{model.sid}.xml"
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
