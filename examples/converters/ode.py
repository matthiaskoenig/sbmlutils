"""Export of an SBML model as its system of ordinary differential equations.

`sbmlutils.converters.ode` writes the ODE system of a model as code which simulates
it (python, julia, R) and as documents which describe it (typst, LaTeX, markdown).
The example writes all six formats of the repressilator of Elowitz and Leibler
(BIOMD0000000012), the markdown in addition as a fragment to include into a document
of its own (`standalone=False`), compiles the typst document to SVG, one file per
page, if the `typst` package is installed (part of the `dev` extra), and simulates
the model with the generated python code.

Run it from the root of the repository:

```bash
python -m examples.converters.ode                    # into the working directory
python -m examples.converters.ode docs/images/ode    # the files of the documentation
```

The files are written into the current working directory, or into the directory
given as the argument. The documentation page `docs/ode.md` shows the files in
`docs/images/ode`, which are written by this example.
"""

import runpy
import sys
from pathlib import Path

import pandas as pd

from sbmlutils.console import console
from sbmlutils.converters.ode import FORMATS, OdeSystem
from sbmlutils.resources import REPRESSILATOR_SBML

#: the file suffix of every format, in the order of `FORMATS`
SUFFIXES: dict[str, str] = {name: fmt.suffixes[0] for name, fmt in FORMATS.items()}


def export(sbml_path: Path, output_dir: Path, name: str) -> list[Path]:
    """Write the ODE system of a model in all formats.

    Args:
        sbml_path: the SBML model
        output_dir: the directory the files are written to
        name: the name of the files, e.g. `repressilator` for `repressilator.py`

    Returns:
        the paths of the files: one per format, then the markdown fragment
    """
    system = OdeSystem.from_sbml(sbml_path)
    paths = [
        system.write(output_dir / f"{name}{suffix}") for suffix in SUFFIXES.values()
    ]
    # the markdown as a fragment to include into another document, as docs/ode.md does
    paths.append(system.write(output_dir / f"{name}_fragment.md", standalone=False))
    return paths


def compile_typst(typ_path: Path) -> list[Path]:
    """Compile a typst document to SVG, one file per page.

    The pages are written next to the document, `<name>-1.svg`, `<name>-2.svg`, ...;
    the pages of an earlier compilation are removed first. Nothing is compiled if the
    `typst` package is not installed.

    Args:
        typ_path: the typst document

    Returns:
        the paths of the pages, empty without the `typst` package
    """
    try:
        import typst
    except ImportError:
        console.print("The typst document is not compiled, `pip install typst`.")
        return []
    for page in typ_path.parent.glob(f"{typ_path.stem}-*.svg"):
        page.unlink()
    # the fonts of typst only, so that the pages are the same on every machine
    output = typst.compile(str(typ_path), format="svg", ignore_system_fonts=True)
    pages = output if isinstance(output, list) else [output]
    paths = [
        typ_path.with_name(f"{typ_path.stem}-{k}.svg") for k in range(1, len(pages) + 1)
    ]
    for path, page in zip(paths, pages, strict=True):
        path.write_bytes(page)
    return paths


def simulate(py_path: Path, t_end: float) -> pd.DataFrame:
    """Simulate a model with its generated python code.

    Args:
        py_path: the python code of the model, written with `simulator=True`
        t_end: the end time of the simulation

    Returns:
        the time and the states at the time points
    """
    code = runpy.run_path(str(py_path))
    result: pd.DataFrame = code["simulate"](t_end=t_end)
    return result[["time", *code["XIDS"]]]


def example(sbml_path: Path, output_dir: Path, name: str) -> list[Path]:
    """Write the ODE system of a model in all formats and simulate it.

    Args:
        sbml_path: the SBML model
        output_dir: the directory the files are written to
        name: the name of the files

    Returns:
        the paths of the files, the pages of the typst document included
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = export(sbml_path, output_dir, name)
    paths.extend(compile_typst(output_dir / f"{name}.typ"))
    for path in paths:
        console.print(f"written {path}")

    result = simulate(output_dir / f"{name}.py", t_end=1000.0)
    console.rule("the states of the simulation", style="white")
    console.print(result.iloc[::10].to_string(index=False))
    return paths


if __name__ == "__main__":
    from sbmlutils import log

    log.enable_rich_logging()

    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    example(sbml_path=REPRESSILATOR_SBML, output_dir=output, name="repressilator")
