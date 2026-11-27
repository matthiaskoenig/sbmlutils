"""The ODE export of sbmlutils is the shared Rust generator, which it re-exports."""

import importlib
import subprocess
import sys
import warnings
from pathlib import Path

import pytest
from sbmlsim_core import ode as core_ode

from sbmlutils.factory import (
    Compartment,
    Model,
    Parameter,
    Reaction,
    Species,
    create_model,
)
from sbmlutils.resources import REPRESSILATOR_SBML
from sbmlutils.validation import ValidationOptions

with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore",
        message=r"sbmlutils\.converters\.ode is deprecated",
        category=DeprecationWarning,
    )
    ode = importlib.import_module("sbmlutils.converters.ode")


@pytest.mark.parametrize(
    "statement",
    [
        "from sbmlutils.converters import ode",
        "from sbmlutils.converters.ode import OdeSystem",
        "from sbmlutils.converters.ode.system import OdeSystem",
    ],
)
def test_deprecated_import_warns_at_the_call_site(statement: str) -> None:
    """Every legacy import path warns once in a fresh application process."""
    code = (
        "import warnings\n"
        "with warnings.catch_warnings(record=True) as caught:\n"
        "    warnings.simplefilter('always', DeprecationWarning)\n"
        f"    {statement}\n"
        "assert len(caught) == 1, caught\n"
        "warning = caught[0]\n"
        "assert warning.category is DeprecationWarning\n"
        "assert str(warning.message) == "
        "'sbmlutils.converters.ode is deprecated; import from sbmlsim_core instead.'\n"
        "assert warning.filename == '<string>', warning.filename\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_reexport() -> None:
    """The public API of `sbmlutils.converters.ode` is that of core_ode."""
    assert ode.OdeSystem is core_ode.OdeSystem
    assert ode.FORMATS is core_ode.FORMATS
    assert ode.Format is core_ode.Format
    assert ode.render is core_ode.render
    assert ode.render_template is core_ode.render_template
    assert ode.write is core_ode.write


@pytest.mark.parametrize(
    "submodule",
    ["system", "formats"],
)
def test_submodules_are_the_shared_core(submodule: str) -> None:
    """`import sbmlutils.converters.ode.<submodule>` gives the module of core_ode."""
    module = importlib.import_module(f"sbmlutils.converters.ode.{submodule}")
    assert module is core_ode


def test_from_import_of_a_submodule() -> None:
    """A name is imported from a submodule as it was before the move.

    The submodules exist at runtime only, a type checker does not see them.
    """
    # registered in `sys.modules` by `sbmlutils.converters.ode`
    from sbmlutils.converters.ode.system import (  # ty: ignore[import-not-found]
        OdeSystem,
    )

    assert OdeSystem is core_ode.OdeSystem


def test_render_markdown() -> None:
    """The repressilator renders to markdown with its ODEs."""
    system = ode.OdeSystem.from_sbml(REPRESSILATOR_SBML)
    markdown = system.render("markdown")
    assert r"\frac{\mathrm{d}" in markdown


def test_create_model_markdown(tmp_path: Path) -> None:
    """`create_model(create_markdown=True)` writes the markdown of core_ode."""
    model = Model(
        sid="markdown",
        compartments=[Compartment(sid="c", value=1.0)],
        species=[Species(sid="S1", initialConcentration=10.0, compartment="c")],
        parameters=[Parameter(sid="k1", value=0.1)],
        reactions=[Reaction(sid="J0", equation="S1 -> ", formula="k1 * S1")],
    )
    result = create_model(
        model=model,
        filepath=tmp_path / "model.xml",
        validation_options=ValidationOptions(units_consistency=False),
        create_markdown=True,
    )
    assert result.markdown_path == tmp_path / "model.md"
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert r"\frac{\mathrm{d}" in markdown
    assert "sbmlsim-core" in markdown
