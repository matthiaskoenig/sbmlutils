"""Utilities for the creation and work with layout models."""
from typing import Dict, List, Optional

import libsbml

import sbmlutils.factory as factory
from sbmlutils.factory import SBML_LEVEL, SBML_VERSION


__all__ = [
    "LAYOUT_VERSION",
    "LAYOUT_ROLE_SUBSTRATE",
    "LAYOUT_ROLE_PRODUCT",
    "LAYOUT_ROLE_SIDESUBSTRATE",
    "LAYOUT_ROLE_SIDEPRODUCT",
    "LAYOUT_ROLE_MODIFIER",
    "LAYOUT_ROLE_ACTIVATOR",
    "LAYOUT_ROLE_INHIBITOR",
    "LAYOUT_ROLE_UNDEFINED",
    "Layout",
    "SpeciesGlyph",
    "ReactionGlyph",
    "CompartmentGlyph",
]

LAYOUT_VERSION = 1

LAYOUT_ROLE_SUBSTRATE = "substrate"
LAYOUT_ROLE_PRODUCT = "product"
LAYOUT_ROLE_SIDESUBSTRATE = "sidesubstrate"
LAYOUT_ROLE_SIDEPRODUCT = "sideproduct"
LAYOUT_ROLE_MODIFIER = "modifier"
LAYOUT_ROLE_ACTIVATOR = "activator"
LAYOUT_ROLE_INHIBITOR = "inhibitor"
LAYOUT_ROLE_UNDEFINED = "undefined"


class SpeciesGlyph(factory.Sbase):
    """SpeciesGlyph."""

    def __init__(
        self,
        sid: str,
        species: str,
        x: float,
        y: float,
        z: float = 0,
        w: float = 50,
        h: float = 20,
        d: float = 0,
        text: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
    ):
        super(SpeciesGlyph, self).__init__(
            sid=sid, name=name, sboTerm=sboTerm, metaId=metaId
        )
        self.species = species
        self.x = x
        self.y = y
        self.z = z
        self.width = w
        self.height = h
        self.depth = d
        self.text = text

    def _set_glyph_fields(
        self, obj: libsbml.SpeciesGlyph, layout: libsbml.Layout, model: libsbml.Model
    ) -> None:
        """Set fields."""
        super(SpeciesGlyph, self)._set_fields(obj, model)
        obj.setSpeciesId(self.species)
        bb = _create_bounding_box(
            x=self.x,
            y=self.y,
            z=self.z,
            width=self.width,
            height=self.height,
            depth=self.depth,
        )
        obj.setBoundingBox(bb)
        # text glyph
        t_glyph = layout.createTextGlyph()
        t_glyph.setId(f"tglyph_{self.sid}")
        t_glyph.setGraphicalObjectId(self.sid)
        t_glyph.setText(self.text)

        bb = _create_bounding_box(
            x=self.x,
            y=self.y,
            z=self.z,
            width=self.width,
            height=self.height,
            depth=self.depth,
        )
        t_glyph.setBoundingBox(bb)


class CompartmentGlyph(factory.Sbase):
    """CompartmentGlyph."""

    def __init__(
        self,
        sid: str,
        compartment: str,
        x: float,
        y: float,
        z: float = 0,
        w: float = 200,
        h: float = 200,
        d: float = 0,
        text: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
    ):
        super(CompartmentGlyph, self).__init__(
            sid=sid, name=name, sboTerm=sboTerm, metaId=metaId
        )
        self.compartment = compartment
        self.x = x
        self.y = y
        self.z = z
        self.width = w
        self.height = h
        self.depth = d
        self.text = text

    def _set_glyph_fields(
        self, obj: libsbml.SpeciesGlyph, layout: libsbml.Layout, model: libsbml.Model
    ) -> None:
        """Set fields."""
        super(CompartmentGlyph, self)._set_fields(obj, model)
        obj.setCompartmentId(self.compartment)
        bb = _create_bounding_box(
            x=self.x,
            y=self.y,
            z=self.z,
            width=self.width,
            height=self.height,
            depth=self.depth,
        )
        obj.setBoundingBox(bb)
        # text glyph
        t_glyph = layout.createTextGlyph()
        t_glyph.setId(f"tglyph_{self.sid}")
        t_glyph.setGraphicalObjectId(self.sid)
        t_glyph.setText(self.text)
        bb = _create_bounding_box(
            x=self.x,
            y=self.y,
            z=self.z,
            width=self.width,
            height=self.height,
            depth=self.depth,
        )
        t_glyph.setBoundingBox(bb)


class ReactionGlyph(factory.Sbase):
    """ReactionGlyph."""

    def __init__(
        self,
        sid: str,
        reaction: str,
        x: float,
        y: float,
        z: float = 0,
        species_glyphs: Dict[str, str] = None,
        w: float = 20,
        h: float = 20,
        d: float = 0,
        text: Optional[str] = None,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
    ):
        super(ReactionGlyph, self).__init__(
            sid=sid, name=name, sboTerm=sboTerm, metaId=metaId
        )
        self.reaction: str = reaction
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.width: float = w
        self.height: float = h
        self.depth: float = d

        self.text: Optional[str] = text
        self.species_glyphs: Dict[str, str] = species_glyphs if species_glyphs else {}

        self.layout = None

    def _set_glyph_fields(
        self, obj: libsbml.ReactionGlyph, layout: libsbml.Layout, model: libsbml.Model
    ) -> None:
        super(ReactionGlyph, self)._set_fields(obj, model)
        self.layout = layout
        obj.setReactionId(self.reaction)
        bb = _create_bounding_box(
            x=self.x,
            y=self.y,
            z=self.z,
            width=self.width,
            height=self.height,
            depth=self.depth,
        )
        obj.setBoundingBox(bb)

        # text glyph
        t_glyph = layout.createTextGlyph()
        t_glyph.setId(f"tglyph_{self.sid}")
        t_glyph.setGraphicalObjectId(self.sid)
        t_glyph.setText(self.text)
        bb = _create_bounding_box(
            x=self.x, y=self.y, z=self.z, width=0, height=0, depth=0
        )
        t_glyph.setBoundingBox(bb)

        # get direction of reaction
        eps = 1e-6
        x_tot = 0
        y_tot = 0
        x_r = bb.getX()
        y_r = bb.getY()
        for sg_id, role in self.species_glyphs.items():
            s_glyph: libsbml.SpeciesGlyph = layout.getSpeciesGlyph(sg_id)
            s_bb: libsbml.BoundingBox = s_glyph.getBoundingBox()
            x_s = s_bb.getX()
            y_s = s_bb.getY()
            if role in [LAYOUT_ROLE_SIDESUBSTRATE, LAYOUT_ROLE_SUBSTRATE]:
                x_tot += x_r - x_s
                y_tot += y_r - y_s
            elif role in [LAYOUT_ROLE_PRODUCT, LAYOUT_ROLE_SIDEPRODUCT]:
                x_tot += x_s - x_r
                y_tot += y_s - y_r

        if (abs(x_tot) < eps) and (abs(y_tot) < eps):
            direction = "down"
        else:
            if abs(x_tot) >= abs(y_tot):
                if x_tot >= 0:
                    direction = "right"
                elif x_tot < 0:
                    direction = "left"
            elif abs(x_tot) < abs(y_tot):
                if y_tot >= 0:
                    direction = "down"
                elif x_tot > 0:
                    direction = "up"

        # create speciesReferenceGlyphs
        for sg_id, role in self.species_glyphs.items():
            srg: libsbml.SpeciesReferenceGlyph = obj.createSpeciesReferenceGlyph()
            srg.setId(obj.getId() + "__" + sg_id)
            srg.setSpeciesGlyphId(sg_id)
            srg.setRole(role)

            self._create_curve(layout, srg, obj.getId(), sg_id, role, direction)

    def _create_curve(
        self,
        layout: libsbml.Layout,
        srg: libsbml.SpeciesReferenceGlyph,
        r_glyph_id: str,
        s_glyph_id: str,
        role: str,
        direction: str,
    ) -> None:
        """Heuristic for creating the curves.

        :param layout:
        :param srg:
        :param r_glyph_id:
        :param s_glyph_id:
        :param role:
        :return:
        """

        # 1. Find the direction of the reaction (via location of substrates and
        # 2. Orient the curves accordingly (at the bounding box, with all ingoing connecting
        # at same point and all outgoing connecting at same point.
        r_glyph: libsbml.ReactionGlyph = layout.getReactionGlyph(r_glyph_id)
        s_glyph: libsbml.SpeciesGlyph = layout.getSpeciesGlyph(s_glyph_id)

        # create curve
        line_segment: libsbml.LineSegment = srg.createLineSegment()

        # calculate start and end points for line
        s_bb: libsbml.BoundingBox = s_glyph.getBoundingBox()
        r_bb: libsbml.BoundingBox = r_glyph.getBoundingBox()

        x, y, h, w = r_bb.getX(), r_bb.getY(), r_bb.getHeight(), r_bb.getWidth()
        xs, ys, hs, ws = s_bb.getX(), s_bb.getY(), s_bb.getHeight(), s_bb.getWidth()
        if direction == "right":
            s_point_substrate = (xs + ws, ys + 0.5 * hs)
            s_point_product = (xs, ys + 0.5 * hs)
            s_point_modifier = (xs + 0.5 * ws, y + hs)

            r_point_substrate = (x, y + 0.5 * h)
            r_point_product = (x + w, y + 0.5 * h)
            r_point_modifier = (x + 0.5 * w, y)
        elif direction == "left":
            s_point_substrate = (xs, ys + 0.5 * hs)
            s_point_product = (xs + ws, ys + 0.5 * hs)
            s_point_modifier = (xs + 0.5 * ws, y + hs)

            r_point_substrate = (x + w, y + 0.5 * h)
            r_point_product = (x, y + 0.5 * h)
            r_point_modifier = (x + 0.5 * w, y)
        elif direction == "down":
            s_point_substrate = (xs + 0.5 * ws, ys + hs)
            s_point_product = (xs + 0.5 * ws, ys)
            s_point_modifier = (xs, ys + 0.5 * hs)

            r_point_substrate = (x + 0.5 * w, y)
            r_point_product = (x + 0.5 * w, y + h)
            r_point_modifier = (x + w, y + 0.5 * h)
        elif direction == "up":
            s_point_substrate = (xs + 0.5 * ws, ys)
            s_point_product = (xs + 0.5 * ws, ys + hs)
            s_point_modifier = (xs, ys + 0.5 * hs)

            r_point_substrate = (x + 0.5 * w, y + h)
            r_point_product = (x + 0.5 * w, y)
            r_point_modifier = (x + w, y + 0.5 * h)

        if role in [LAYOUT_ROLE_ACTIVATOR, LAYOUT_ROLE_INHIBITOR, LAYOUT_ROLE_MODIFIER]:
            # segment from species -> reaction
            line_segment.setStart(s_point_modifier[0], s_point_modifier[1], 0)
            line_segment.setEnd(r_point_modifier[0], r_point_modifier[1], 0)
        elif role in [
            LAYOUT_ROLE_SUBSTRATE,
            LAYOUT_ROLE_SIDESUBSTRATE,
            LAYOUT_ROLE_UNDEFINED,
        ]:
            # segment from reaction -> species
            line_segment.setEnd(s_point_substrate[0], s_point_substrate[1], 0)
            line_segment.setStart(r_point_substrate[0], r_point_substrate[1], 0)
        elif role in [LAYOUT_ROLE_PRODUCT, LAYOUT_ROLE_SIDEPRODUCT]:
            # segment from reaction -> species
            line_segment.setEnd(s_point_product[0], s_point_product[1], 0)
            line_segment.setStart(r_point_product[0], r_point_product[1], 0)


class Layout(factory.Sbase):
    """Layout."""

    def __init__(
        self,
        sid: str,
        width: float,
        height: float,
        compartment_glyphs: Optional[List[CompartmentGlyph]] = None,
        species_glyphs: Optional[List[SpeciesGlyph]] = None,
        reaction_glyphs: Optional[List[ReactionGlyph]] = None,
        depth: int = 0,
        name: Optional[str] = None,
        sboTerm: Optional[str] = None,
        metaId: Optional[str] = None,
    ):
        """Create a layout."""
        super(Layout, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.width = float(width)
        self.height = float(height)
        self.depth = float(depth)
        self.compartment_glyphs = compartment_glyphs if compartment_glyphs else []
        self.species_glyphs = species_glyphs if species_glyphs else []
        self.reaction_glyphs = reaction_glyphs if reaction_glyphs else []

    def create_sbml(self, model: libsbml.Model) -> libsbml.Layout:
        """Create SBML in model."""
        layout_model: libsbml.LayoutModelPlugin = model.getPlugin("layout")
        if not layout_model:
            doc: libsbml.SBML_RULE = model.getSBMLDocument()
            doc.enablePackage(
                f"http://www.sbml.org/sbml/level3/version1/layout/version{LAYOUT_VERSION}",
                "layout",
                True,
            )
            doc.setPackageRequired("layout", False)
            layout_model = model.getPlugin("layout")

        layout: libsbml.Layout = layout_model.createLayout()
        self._set_fields(layout, model)

        return layout

    def _set_fields(self, obj: libsbml.Layout, model: libsbml.Model) -> None:
        super(Layout, self)._set_fields(obj, model)
        dim: libsbml.Dimensions = libsbml.Dimensions(
            SBML_LEVEL,
            SBML_VERSION,
            LAYOUT_VERSION,  # FIXME: use settings in constructors
        )
        dim.setWidth(self.width)
        dim.setHeight(self.height)
        dim.setDepth(self.depth)
        obj.setDimensions(dim)

        for s_item in self.species_glyphs:
            s_glyph: libsbml.SpeciesGlyph = obj.createSpeciesGlyph()
            s_item._set_glyph_fields(s_glyph, obj, model)

        for r_item in self.reaction_glyphs:
            r_glyph: libsbml.ReactionGlyph = obj.createReactionGlyph()
            r_item._set_glyph_fields(r_glyph, obj, model)


def _create_bounding_box(
    x: float, y: float, width: float, height: float, z: float = 0, depth: float = 0
) -> libsbml.BoundingBox:
    """Create the BoundingBox object."""
    bb: libsbml.BoundingBox = libsbml.BoundingBox(
        SBML_LEVEL, SBML_VERSION, LAYOUT_VERSION
    )
    bb.setX(float(x))
    bb.setY(float(y))
    bb.setZ(float(z))
    bb.setWidth(float(width))
    bb.setHeight(float(height))
    bb.setDepth(float(depth))
    return bb
