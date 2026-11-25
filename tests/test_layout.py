"""Check that complete layout diagrams survive writing and reading SBML."""

from pathlib import Path

import pytest

from sbmlutils import layout
from sbmlutils.factory import (
    Compartment,
    Model,
    ModelUnits,
    Reaction,
    Species,
    Units,
    create_model,
)
from sbmlutils.io import read_sbml
from sbmlutils.validation import validate_doc


def _model(diagram: layout.Layout) -> Model:
    """Create a pathway with the supplied diagram."""
    return Model(
        sid="pathway",
        model_units=ModelUnits(
            time=Units.second,
            substance=Units.mole,
            extent=Units.mole,
            volume=Units.litre,
        ),
        compartments=[Compartment("cell", value=1.0, unit=Units.litre)],
        species=[
            Species("A", compartment="cell", initialAmount=1.0),
            Species("B", compartment="cell", initialAmount=0.0),
        ],
        reactions=[Reaction("step", equation="A -> B")],
        layouts=[diagram],
    )


def test_compartment_glyph_is_written_with_its_label_and_geometry(
    tmp_path: Path,
) -> None:
    """A compartment boundary and label remain present in the written diagram."""
    diagram = layout.Layout(
        "diagram",
        width=300,
        height=120,
        compartment_glyphs=[
            layout.CompartmentGlyph(
                "glyph_cell", "cell", x=5, y=10, w=290, h=100, text="Cell"
            )
        ],
    )
    result = create_model(
        _model(diagram), tmp_path / "compartment.xml", raise_on_error=True
    )
    doc = read_sbml(result.sbml_path)
    stored = doc.getModel().getPlugin("layout").getLayout(0)

    assert stored.getNumCompartmentGlyphs() == 1
    glyph = stored.getCompartmentGlyph("glyph_cell")
    assert glyph.getCompartmentId() == "cell"
    box = glyph.getBoundingBox()
    assert (box.getX(), box.getY(), box.getWidth(), box.getHeight()) == (
        5,
        10,
        290,
        100,
    )
    label = stored.getTextGlyph("tglyph_glyph_cell")
    assert label.getGraphicalObjectId() == "glyph_cell"
    assert label.getText() == "Cell"
    assert not validate_doc(doc).errors


def test_upward_reaction_is_written_with_connected_species_glyphs(
    tmp_path: Path,
) -> None:
    """A vertical pathway with the product above the substrate remains writable."""
    diagram = layout.Layout(
        "upward",
        width=200,
        height=250,
        species_glyphs=[
            layout.SpeciesGlyph("glyph_A", "A", x=75, y=200, text="A"),
            layout.SpeciesGlyph("glyph_B", "B", x=75, y=20, text="B"),
        ],
        reaction_glyphs=[
            layout.ReactionGlyph(
                "glyph_step",
                "step",
                x=75,
                y=110,
                species_glyphs={
                    "glyph_A": layout.LAYOUT_ROLE_SUBSTRATE,
                    "glyph_B": layout.LAYOUT_ROLE_PRODUCT,
                },
                text="Step",
            )
        ],
    )
    result = create_model(_model(diagram), tmp_path / "upward.xml", raise_on_error=True)
    doc = read_sbml(result.sbml_path)
    reaction = doc.getModel().getPlugin("layout").getLayout(0).getReactionGlyph(0)

    assert reaction.getNumSpeciesReferenceGlyphs() == 2
    for index, species_id in enumerate(("glyph_A", "glyph_B")):
        reference = reaction.getSpeciesReferenceGlyph(index)
        assert reference.getSpeciesGlyphId() == species_id
        assert reference.getCurve().getNumCurveSegments() == 1
    assert not validate_doc(doc).errors


@pytest.mark.parametrize("axis", ["horizontal", "vertical"])
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
def test_modifier_curves_touch_facing_glyph_edges(
    tmp_path: Path, axis: str, reverse: bool
) -> None:
    """Modifiers connect to the nearest perpendicular edge of the reaction."""
    if axis == "horizontal":
        first, last = (35, 50), (215, 50)
        modifiers = [
            ("E", layout.LAYOUT_ROLE_MODIFIER, (100, 10), (125, 30), (150, 50)),
            ("F", layout.LAYOUT_ROLE_ACTIVATOR, (120, 120), (145, 120), (150, 70)),
        ]
    else:
        first, last = (140, 10), (140, 150)
        modifiers = [
            ("E", layout.LAYOUT_ROLE_INHIBITOR, (35, 80), (85, 90), (140, 60)),
            ("F", layout.LAYOUT_ROLE_MODIFIER, (230, 70), (230, 80), (160, 60)),
        ]
    substrate, product = (last, first) if reverse else (first, last)
    roles = {
        "glyph_A": layout.LAYOUT_ROLE_SUBSTRATE,
        "glyph_B": layout.LAYOUT_ROLE_PRODUCT,
        **{f"glyph_{sid}": role for sid, role, *_ in modifiers},
    }
    diagram = layout.Layout(
        "diagram",
        width=300,
        height=180,
        species_glyphs=[
            layout.SpeciesGlyph("glyph_A", "A", x=substrate[0], y=substrate[1]),
            layout.SpeciesGlyph("glyph_B", "B", x=product[0], y=product[1]),
            *[
                layout.SpeciesGlyph(f"glyph_{sid}", sid, x=position[0], y=position[1])
                for sid, _, position, _, _ in modifiers
            ],
        ],
        reaction_glyphs=[
            layout.ReactionGlyph(
                "glyph_step", "step", x=140, y=50, species_glyphs=roles
            )
        ],
    )
    model = _model(diagram)
    model.species.extend(
        Species(sid, compartment="cell", initialAmount=0.1, boundaryCondition=True)
        for sid, *_ in modifiers
    )
    model.reactions = [Reaction("step", equation="A -> B [E, F]")]
    result = create_model(model, tmp_path / "modifiers.xml", raise_on_error=True)
    doc = read_sbml(result.sbml_path)
    reaction = doc.getModel().getPlugin("layout").getLayout(0).getReactionGlyph(0)
    references = reaction.getListOfSpeciesReferenceGlyphs()

    for sid, role, _, expected_start, expected_end in modifiers:
        reference = references.get(f"glyph_step__glyph_{sid}")
        assert reference.getSpeciesGlyphId() == f"glyph_{sid}"
        assert reference.getRoleString() == role
        curve = reference.getCurve()
        assert curve.getNumCurveSegments() == 1
        segment = curve.getCurveSegment(0)
        start, end = segment.getStart(), segment.getEnd()
        assert (start.getXOffset(), start.getYOffset()) == expected_start
        assert (end.getXOffset(), end.getYOffset()) == expected_end
    assert not validate_doc(doc).errors


@pytest.mark.parametrize("without_label", ["compartment", "species", "reaction"])
def test_glyphs_without_optional_text_preserve_geometry(
    tmp_path: Path, without_label: str
) -> None:
    """Omitting text keeps the glyph and does not create an empty text glyph."""
    compartment = layout.CompartmentGlyph(
        "glyph_cell", "cell", x=5, y=5, w=290, h=110, text="Cell"
    )
    species = layout.SpeciesGlyph("glyph_A", "A", x=35, y=50, text="A")
    reaction = layout.ReactionGlyph(
        "glyph_step",
        "step",
        x=140,
        y=50,
        species_glyphs={
            "glyph_A": layout.LAYOUT_ROLE_SUBSTRATE,
            "glyph_B": layout.LAYOUT_ROLE_PRODUCT,
        },
        text="Step",
    )
    glyph = {"compartment": compartment, "species": species, "reaction": reaction}[
        without_label
    ]
    glyph.text = None
    diagram = layout.Layout(
        "diagram",
        width=300,
        height=120,
        compartment_glyphs=[compartment],
        species_glyphs=[
            species,
            layout.SpeciesGlyph("glyph_B", "B", x=215, y=50, text="B"),
        ],
        reaction_glyphs=[reaction],
    )
    result = create_model(
        _model(diagram), tmp_path / "optional_text.xml", raise_on_error=True
    )
    doc = read_sbml(result.sbml_path)
    stored = doc.getModel().getPlugin("layout").getLayout(0)

    assert stored.getNumCompartmentGlyphs() == 1
    assert stored.getNumSpeciesGlyphs() == 2
    assert stored.getNumReactionGlyphs() == 1
    assert stored.getNumTextGlyphs() == 3
    assert stored.getTextGlyph(f"tglyph_{glyph.sid}") is None
    assert not validate_doc(doc).errors
