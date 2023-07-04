"""Example of creating markdown and python code."""
from pathlib import Path

from sbmlutils.console import console
from sbmlutils.converters import odefac


if __name__ == "__main__":
    for model_id in [
        "iri_liver",
        # "pancreas_deepa"
    ]:
        base_dir = Path(__file__).parent / "odefac_example"
        model_path = base_dir / f"{model_id}.xml"

        # Create ODE system
        md_path = base_dir / f"{model_id}.md"
        py_path = base_dir / f"{model_id}.py"

        factory = odefac.SBML2ODE.from_file(sbml_file=model_path)
        factory.to_markdown(md_file=md_path)
        factory.to_python(py_file=py_path)

        console.rule(style="white")
        with open(md_path, "r") as f_ode:
            console.print(str(f_ode.read()).replace("[", r"\["))
        console.rule(style="white")
