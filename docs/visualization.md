# Visualization

A reaction network is easier to check as a picture than as XML. `sbmlutils.cytoscape` sends a model to a running [Cytoscape](https://cytoscape.org) instance and renders it as a network.

## Requirements

The visualization needs two things which do not come with `sbmlutils`:

```bash
pip install sbmlutils[cytoscape]
```

installs [py4cytoscape](https://py4cytoscape.readthedocs.io), which talks to the CyREST interface, and Cytoscape itself has to be **running** on the machine — download it from [cytoscape.org](https://cytoscape.org). The [cy3sbml](https://github.com/matthiaskoenig/cy3sbml) app reads the SBML, install it from the Cytoscape app store.

If py4cytoscape is not installed, or Cytoscape is not reachable, the functions log a warning and return `None`; they do not raise, so a model creation script which visualizes at the end still finishes.

## Visualizing a model

```python
from pathlib import Path

from sbmlutils.cytoscape import visualize_sbml

visualize_sbml(sbml_path=Path("model.xml"))
```

`delete_session=True` closes what is open in Cytoscape before the model is loaded, which keeps a script from piling up networks:

```python
visualize_sbml(sbml_path=Path("model.xml"), delete_session=True)
```

Antimony is visualized without writing an SBML file first:

```python
from sbmlutils.cytoscape import visualize_antimony

visualize_antimony("J0: S1 -> S2; k1*S1; S1 = 10; S2 = 0; k1 = 0.1")
```

Most model examples end with a call to `visualize_sbml`, so running one shows the network it just built.

## Layout

The positions of the nodes are read from and applied to a network:

```python
from sbmlutils.cytoscape import apply_layout, read_layout_xml

layout = read_layout_xml(sbml_path=Path("model.xml"), xml_path=Path("layout.xml"))
apply_layout(layout)
```

`read_layout_xml` returns the positions as a `DataFrame`, so a layout is edited, generated or stored like any other table.

## Annotations on the canvas

Shapes and text are drawn on the canvas of the network, e.g. to group a pathway or to label a compartment:

```python
from sbmlutils.cytoscape import (
    AnnotationShape,
    AnnotationShapeType,
    AnnotationText,
    add_annotations,
)

add_annotations(
    [
        AnnotationShape(
            type=AnnotationShapeType.ROUND_RECTANGLE,
            x_pos=100,
            y_pos=100,
            width=400,
            height=300,
            fill_color="#EEEEEE",
        ),
        AnnotationText(text="cytosol", x_pos=120, y_pos=110, font_size=24),
    ]
)
```

## Exporting an image

```python
from sbmlutils.cytoscape import export_image

export_image(image_path=Path("network.png"), format="PNG")
```

## The SBML layout package

The positions of a model can also be stored *in* the model, with the SBML layout package. `sbmlutils.layout` provides the objects for it — `Layout`, `SpeciesGlyph`, `ReactionGlyph`, `CompartmentGlyph` — which are assigned to `model.layouts`:

```python
import sbmlutils.layout as layout

model.layouts = [
    layout.Layout(
        sid="layout_1",
        name="Layout 1",
        width=700,
        height=700,
        compartment_glyphs=[
            layout.CompartmentGlyph("glyph_c", compartment="c", x=5, y=5, w=690, h=690)
        ],
    )
]
```

`examples/tiny/tiny.py` builds a complete layout this way.
