# layout

The SBML layout package stores a diagram alongside the model. A layout defines a canvas and glyphs that refer to compartments, species, and reactions. Compatible viewers can use those positions and connections to draw the network.

## The SBML layout package

The factory writes the entries in `Model.layouts` into the SBML document. Each compartment and species glyph refers to its model element by ID. A reaction glyph refers to a reaction ID and connects to **glyph** IDs, which lets a layout show the same species in more than one place.

```python
from pathlib import Path

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

model = Model(
    sid="pathway",
    model_units=ModelUnits(substance=Units.mole, volume=Units.litre),
    compartments=[Compartment("cell", value=1.0, unit=Units.litre)],
    species=[
        Species("A", compartment="cell", initialAmount=1.0),
        Species("B", compartment="cell", initialAmount=0.0),
    ],
    reactions=[Reaction("step", equation="A -> B")],
    layouts=[
        layout.Layout(
            sid="pathway_layout",
            width=300,
            height=120,
            compartment_glyphs=[
                layout.CompartmentGlyph("glyph_cell", "cell", x=5, y=5, w=290, h=110)
            ],
            species_glyphs=[
                layout.SpeciesGlyph("glyph_A", "A", x=35, y=50, text="A"),
                layout.SpeciesGlyph("glyph_B", "B", x=215, y=50, text="B"),
            ],
            reaction_glyphs=[
                layout.ReactionGlyph(
                    "glyph_step",
                    "step",
                    x=140,
                    y=50,
                    text="Step",
                    species_glyphs={
                        "glyph_A": layout.LAYOUT_ROLE_SUBSTRATE,
                        "glyph_B": layout.LAYOUT_ROLE_PRODUCT,
                    },
                )
            ],
        )
    ],
)
result = create_model(model, Path("pathway_layout.xml"), raise_on_error=True)

doc = read_sbml(result.sbml_path)
stored_layout = doc.getModel().getPlugin("layout").getLayout(0)
assert stored_layout.getNumSpeciesGlyphs() == 2
assert stored_layout.getReactionGlyph(0).getNumSpeciesReferenceGlyphs() == 2
```

The layout describes geometry. The reaction equation still defines the model's stoichiometry. The layout is carried by `read_sbml` and `write_sbml` through libSBML. To edit an existing document while preserving its layout, use those functions together with the libSBML layout plugin. The factory parser `sbml_to_model` omits layouts.

See the [layout API](../api/layout.layout.md) for the glyph classes and `python -m examples.tiny.tiny` for a larger pathway diagram.
