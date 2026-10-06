"""The ODE export of sbmlutils is the package sbmlode, which it re-exports."""

import importlib
from pathlib import Path

import pytest
import sbmlode

from sbmlutils.converters import ode
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


def test_reexport() -> None:
    """The public API of `sbmlutils.converters.ode` is that of sbmlode."""
    assert ode.OdeSystem is sbmlode.OdeSystem
    assert ode.FORMATS is sbmlode.FORMATS
    assert ode.Format is sbmlode.Format
    assert ode.render is sbmlode.render
    assert ode.render_template is sbmlode.render_template
    assert ode.write is sbmlode.write


@pytest.mark.parametrize(
    "submodule",
    ["system", "formats", "documents", "symbols", "text", "printers", "printers.latex"],
)
def test_submodules_are_those_of_sbmlode(submodule: str) -> None:
    """`import sbmlutils.converters.ode.<submodule>` gives the module of sbmlode."""
    module = importlib.import_module(f"sbmlutils.converters.ode.{submodule}")
    assert module is importlib.import_module(f"sbmlode.{submodule}")


def test_from_import_of_a_submodule() -> None:
    """A name is imported from a submodule as it was before the move.

    The submodules exist at runtime only, a type checker does not see them.
    """
    # registered in `sys.modules` by `sbmlutils.converters.ode`
    from sbmlutils.converters.ode.system import (  # ty: ignore[unresolved-import]
        OdeSystem,
    )

    assert OdeSystem is sbmlode.OdeSystem


def test_render_markdown() -> None:
    """The repressilator renders to markdown with its ODEs."""
    system = ode.OdeSystem.from_sbml(REPRESSILATOR_SBML)
    markdown = system.render("markdown")
    assert r"\frac{\mathrm{d}" in markdown


def test_create_model_markdown(tmp_path: Path) -> None:
    """`create_model(create_markdown=True)` writes the markdown of sbmlode."""
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
    assert "sbmlode" in markdown
