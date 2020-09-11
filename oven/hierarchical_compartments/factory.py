"""
Midazolam model factory
"""
from pathlib import Path
from pprint import pprint
from sbmlutils.modelcreator import creator
from sbmlutils.comp import flattenSBMLFile
from sbmlutils.report import sbmlreport


def create_model(target_dir, module):
    return creator.create_model(
        modules=[module],
        target_dir=target_dir,
        create_report=True
    )


def create_models(results_path):
    """Creates hierarchical compartment model."""

    # create individual models
    for module in ["model_A"]:
        create_model(target_dir=results_path, module=module)

    # create top_model
    exit()
    [_, _, sbml_path] = create_top_model(results_path)
    sbml_path = Path(sbml_path)
    sbml_path_flat = results_path / "top_model_flat.xml"

    flattenSBMLFile(str(sbml_path.resolve()), output_path=str(sbml_path_flat.resolve()))

    # create model report
    sbmlreport.create_report(str(sbml_path_flat), output_dir=str(results_path))


if __name__ == "__main__":
    results = create_models(Path("."))