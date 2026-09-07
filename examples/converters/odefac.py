"""Conversion of an SBML model into an ODE system.

`sbmlutils.converters.odefac` writes the ODE system of a model as python, R,
julia, markdown or latex, so that a model can be integrated with a solver which
does not read SBML. The example writes the markdown and the python code of a
packaged model.

Run it from the root of the repository:

```bash
python -m examples.converters.odefac
```

The generated files are written into the current working directory.
"""

from pathlib import Path

from sbmlutils.console import console
from sbmlutils.converters import odefac
from sbmlutils.resources import DEMO_SBML


def example(sbml_path: Path, output_dir: Path) -> None:
    """Write the ODE system of a model as markdown and python.

    Args:
        sbml_path: the SBML model to convert
        output_dir: directory the generated files are written to
    """
    md_path = output_dir / f"{sbml_path.stem}.md"
    py_path = output_dir / f"{sbml_path.stem}.py"

    factory = odefac.SBML2ODE.from_file(sbml_file=sbml_path)
    factory.to_markdown(md_file=md_path)
    factory.to_python(py_file=py_path)

    console.rule(style="white")
    console.print(md_path.read_text(encoding="utf-8").replace("[", r"\["))
    console.rule(style="white")


if __name__ == "__main__":
    example(sbml_path=DEMO_SBML, output_dir=Path.cwd())
