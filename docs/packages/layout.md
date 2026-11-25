# layout

The SBML layout package stores a diagram alongside the model. A layout defines a canvas and glyphs that refer to compartments, species, and reactions. Compatible viewers can use those positions and connections to draw the network.

Run the examples in order. The first example saves an unwritten model template for the later diagrams. Other examples edit a document read from an earlier file. Layout coordinates describe drawing geometry; they do not change compartment volumes, species amounts or reaction rates.

## Canvas, compartment, species and reaction glyphs

The factory writes the entries in `Model.layouts` into the SBML document. Each compartment and species glyph refers to its model element by ID. A reaction glyph refers to a reaction ID and connects to **glyph** IDs, which lets a layout show the same species in more than one place.

```python
from copy import deepcopy
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
                layout.CompartmentGlyph(
                    "glyph_cell", "cell", x=5, y=5, w=290, h=110, text="Cell"
                )
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
template = deepcopy(model)
result = create_model(model, Path("pathway_layout.xml"), raise_on_error=True)

doc = read_sbml(result.sbml_path)
stored_layout = doc.getModel().getPlugin("layout").getLayout(0)
assert stored_layout.getNumCompartmentGlyphs() == 1
assert stored_layout.getNumSpeciesGlyphs() == 2
assert stored_layout.getReactionGlyph(0).getNumSpeciesReferenceGlyphs() == 2
```

`Layout.width` and `height` define the canvas. The `x` and `y` of a glyph locate its bounding box, while `w` and `h` give its size. A glyph's own ID identifies a drawing object; `species`, `compartment` or `reaction` identifies the corresponding model element.

## Bounding boxes and text labels

Each factory glyph with `text` creates a `TextGlyph` linked to that graphical object. Inspect the stored geometry and label through the layout plugin:

```python
box = stored_layout.getSpeciesGlyph("glyph_A").getBoundingBox()
assert (box.getX(), box.getY(), box.getWidth(), box.getHeight()) == (35, 50, 50, 20)
label = stored_layout.getTextGlyph("tglyph_glyph_A")
assert label.getGraphicalObjectId() == "glyph_A"
assert label.getText() == "A"
assert stored_layout.getDimensions().getWidth() == 300.0
```

## Repeated species glyphs

A species can appear more than once in a diagram. Give each occurrence its own glyph ID and reuse the species ID. Here the extra drawing of `A` does not add another species to the model or change the reaction stoichiometry.

```python
aliases = deepcopy(template)
aliases.sid = "pathway_aliases"
aliases.layouts[0].species_glyphs.append(
    layout.SpeciesGlyph("glyph_A_again", "A", x=35, y=85, text="A (same species)")
)
result = create_model(aliases, Path("pathway_aliases.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
sbml_model = doc.getModel()
diagram = sbml_model.getPlugin("layout").getLayout(0)
assert sbml_model.getNumSpecies() == 2
assert diagram.getSpeciesGlyph("glyph_A").getSpeciesId() == "A"
assert diagram.getSpeciesGlyph("glyph_A_again").getSpeciesId() == "A"
assert sbml_model.getReaction("step").getNumReactants() == 1
```

## Connections, roles and modifiers

`ReactionGlyph.species_glyphs` maps glyph IDs to roles. The factory creates a `SpeciesReferenceGlyph` and an initial straight-line curve for each connection. `substrate` and `product` indicate the reaction sides. Other available roles include `sidesubstrate`, `sideproduct`, `modifier`, `activator`, `inhibitor` and `undefined`.

This example adds an enzyme to both the reaction's modifier list and the diagram. The `activator` role describes the drawing; it does not supply an enzyme-dependent kinetic law.

```python
activated = deepcopy(template)
activated.sid = "activated_pathway"
activated.species.append(
    Species("E", compartment="cell", initialAmount=0.1, boundaryCondition=True)
)
activated.reactions = [Reaction("step", equation="A -> B [E]")]
diagram = activated.layouts[0]
diagram.height = 180
diagram.compartment_glyphs[0].height = 170
diagram.species_glyphs.append(
    layout.SpeciesGlyph("glyph_E", "E", x=120, y=120, text="Enzyme")
)
diagram.reaction_glyphs[0].species_glyphs["glyph_E"] = layout.LAYOUT_ROLE_ACTIVATOR
result = create_model(activated, Path("activated_pathway.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
sbml_model = doc.getModel()
reaction = sbml_model.getPlugin("layout").getLayout(0).getReactionGlyph("glyph_step")
connection = reaction.getListOfSpeciesReferenceGlyphs().get("glyph_step__glyph_E")
assert connection.getRoleString() == "activator"
assert connection.getSpeciesGlyphId() == "glyph_E"
assert connection.getCurve().getNumCurveSegments() == 1
assert sbml_model.getReaction("step").getModifier(0).getSpecies() == "E"
segment = connection.getCurve().getCurveSegment(0)
assert (segment.getStart().getXOffset(), segment.getStart().getYOffset()) == (145, 120)
assert (segment.getEnd().getXOffset(), segment.getEnd().getYOffset()) == (150, 70)
```

## Multiple layouts of one model

Store alternative views in `Model.layouts`. Both layouts below refer to the same species and reaction, while each layout and each glyph has its own ID. The second diagram places the product above the substrate.

```python
multiple = deepcopy(template)
multiple.sid = "alternative_views"
multiple.layouts.append(
    layout.Layout(
        "vertical",
        width=140,
        height=300,
        compartment_glyphs=[
            layout.CompartmentGlyph(
                "vertical_cell", "cell", x=5, y=5, w=130, h=290, text="Cell"
            )
        ],
        species_glyphs=[
            layout.SpeciesGlyph("vertical_A", "A", x=45, y=210, text="A"),
            layout.SpeciesGlyph("vertical_B", "B", x=45, y=30, text="B"),
        ],
        reaction_glyphs=[
            layout.ReactionGlyph(
                "vertical_step",
                "step",
                x=45,
                y=120,
                text="Step",
                species_glyphs={
                    "vertical_A": layout.LAYOUT_ROLE_SUBSTRATE,
                    "vertical_B": layout.LAYOUT_ROLE_PRODUCT,
                },
            )
        ],
    )
)
result = create_model(multiple, Path("alternative_views.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
plugin = doc.getModel().getPlugin("layout")
assert plugin.getNumLayouts() == 2
assert plugin.getLayout("vertical").getSpeciesGlyph("vertical_A").getSpeciesId() == "A"
```

## Custom curves and labels with libSBML

Use libSBML for graphical constructs beyond the factory's initial glyph placement. This example replaces one straight connection with a cubic Bezier curve. It also adds a label whose `originOfText` refers to a model species, so a viewer can display the species name instead of a fixed text string.

```python
import libsbml

from sbmlutils.io import write_sbml

doc = read_sbml(Path("pathway_layout.xml"))
sbml_model = doc.getModel()
sbml_model.getSpecies("B").setName("Product B")
diagram = sbml_model.getPlugin("layout").getLayout(0)

label = diagram.createTextGlyph()
label.setId("product_name")
label.setGraphicalObjectId("glyph_B")
label.setOriginOfTextId("B")
box = diagram.getSpeciesGlyph("glyph_B").getBoundingBox().clone()
box.setY(85)
box.setWidth(75)
label.setBoundingBox(box)

reaction = diagram.getReactionGlyph("glyph_step")
connection = reaction.getListOfSpeciesReferenceGlyphs().get("glyph_step__glyph_B")
curve = libsbml.Curve(3, 1, 1)
segment = curve.createCubicBezier()
segment.setStart(160, 60)
segment.setBasePoint1(185, 10)
segment.setBasePoint2(200, 10)
segment.setEnd(215, 60)
connection.setCurve(curve)
write_sbml(doc, Path("custom_layout.xml"))

custom_doc = read_sbml(Path("custom_layout.xml"))
diagram = custom_doc.getModel().getPlugin("layout").getLayout(0)
assert diagram.getTextGlyph("product_name").getOriginOfTextId() == "B"
connection = diagram.getReactionGlyph("glyph_step").getSpeciesReferenceGlyph(1)
assert (
    connection.getCurve().getCurveSegment(0).getTypeCode()
    == libsbml.SBML_LAYOUT_CUBICBEZIER
)
```

The curve's start, end and two control points determine its geometry. A `LineSegment` uses just start and end points. These drawing segments do not change the reaction's stoichiometry.

## Three-dimensional geometry

The `Layout` constructor accepts `depth`; glyph constructors accept `z` and `d` for their bounding boxes. On an existing factory glyph, the corresponding size attribute is `depth`. Automatic reaction connectors start in the plane `z=0`, so this example uses libSBML to move the substrate connector's endpoint onto the raised species box. Viewer support determines whether the third dimension is displayed.

```python
spatial_view = deepcopy(template)
spatial_view.sid = "spatial_view"
diagram = spatial_view.layouts[0]
diagram.depth = 80
diagram.compartment_glyphs[0].depth = 80
diagram.species_glyphs[0].z = 10
diagram.species_glyphs[0].depth = 5
result = create_model(spatial_view, Path("spatial_view.xml"), raise_on_error=True)
doc = read_sbml(result.sbml_path)
diagram = doc.getModel().getPlugin("layout").getLayout(0)
connection = diagram.getReactionGlyph("glyph_step").getSpeciesReferenceGlyph(0)
segment = connection.getCurve().getCurveSegment(0)
end = segment.getEnd()
segment.setEnd(end.getXOffset(), end.getYOffset(), 10)
write_sbml(doc, Path("spatial_view.xml"))

spatial_doc = read_sbml(Path("spatial_view.xml"))
diagram = spatial_doc.getModel().getPlugin("layout").getLayout(0)
box = diagram.getSpeciesGlyph("glyph_A").getBoundingBox()
assert diagram.getDimensions().getDepth() == 80.0
assert (box.getZ(), box.getDepth()) == (10.0, 5.0)
connection = diagram.getReactionGlyph("glyph_step").getSpeciesReferenceGlyph(0)
assert connection.getCurve().getCurveSegment(0).getEnd().getZOffset() == box.getZ()
```

`read_sbml` and `write_sbml` preserve layout through libSBML. Keep the `SBMLDocument` alive while editing its graphical objects. The factory parser `sbml_to_model` omits layouts, so use the libSBML document when changing an existing diagram.

See the [layout API](../api/layout.layout.md) for factory signatures and `python -m examples.tiny.tiny` for a larger pathway. Rendering and image export with Cytoscape belong to the [cy3sbml Python package](https://pypi.org/project/cy3sbml/).
