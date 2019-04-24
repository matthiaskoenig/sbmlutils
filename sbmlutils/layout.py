"""
Utilities for the creation and work with layout models.
"""

import libsbml
import sbmlutils.factory as factory
from sbmlutils.factory import SBML_LEVEL, SBML_VERSION

LAYOUT_VERSION = 1

LAYOUT_ROLE_SUBSTRATE = "substrate"
LAYOUT_ROLE_PRODUCT = "product"
LAYOUT_ROLE_SIDESUBSTRATE = "sidesubstrate"
LAYOUT_ROLE_SIDEPRODUCT = "sideproduct"
LAYOUT_ROLE_MODIFIER = "modifier"
LAYOUT_ROLE_ACTIVATOR = "activator"
LAYOUT_ROLE_INHIBITOR = "inhibitor"
LAYOUT_ROLE_UNDEFINED = "undefined"


##########################################################################
# Layout
##########################################################################
class Layout(factory.Sbase):

    def __init__(self, sid, width, height, compartment_glyphs=[], species_glyphs=[], reaction_glyphs=[], depth=0, name=None, sboTerm=None, metaId=None):
        """ Create a layout. """
        super(Layout, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.width = float(width)
        self.height = float(height)
        self.depth = float(depth)
        self.species_glyphs = species_glyphs
        self.reaction_glyphs = reaction_glyphs

    def create_sbml(self, model: libsbml.Model):

        layout_model = model.getPlugin("layout")  # type: libsbml.LayoutModelPlugin
        if not layout_model:
            doc = model.getSBMLDocument()  # type: libsbml.SBMLDocument
            doc.enablePackage("http://www.sbml.org/sbml/level3/version1/layout/version{}".format(LAYOUT_VERSION), "layout", True)
            doc.setPackageRequired("layout", False)
            layout_model = model.getPlugin("layout")  # type: libsbml.LayoutModelPlugin

        layout = layout_model.createLayout()  # type: libsbml.Layout
        self.set_fields(layout)

        return layout

    def set_fields(self, obj: libsbml.Layout):
        super(Layout, self).set_fields(obj)
        dim = libsbml.Dimensions(SBML_LEVEL, SBML_VERSION, LAYOUT_VERSION)  # type: libsbml.Dimensions
        dim.setWidth(self.width)
        dim.setHeight(self.height)
        dim.setDepth(self.depth)
        obj.setDimensions(dim)

        for s_item in self.species_glyphs:
            s_glyph = obj.createSpeciesGlyph()  # type: libsbml.SpeciesGlyph
            s_item.set_fields(s_glyph, obj)

        for r_item in self.reaction_glyphs:
            r_glyph = obj.createReactionGlyph()  # type: libsbml.ReactionGlyph
            r_item.set_fields(r_glyph, obj)


##########################################################################
# SpeciesGlyph
##########################################################################
class SpeciesGlyph(factory.Sbase):
    def __init__(self, sid, species, x, y, z=0, w=50, h=20, d=0, text=None, name=None, sboTerm=None, metaId=None):
        super(SpeciesGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.species = species
        self.x = x
        self.y = y
        self.z = z
        self.width = w
        self.height = h
        self.depth = d
        self.text = text

    def set_fields(self, obj: libsbml.SpeciesGlyph, layout: libsbml.Layout):
        super(SpeciesGlyph, self).set_fields(obj)
        obj.setSpeciesId(self.species)
        bb = _create_bounding_box(x=self.x, y=self.y, z=self.z, width=self.width, height=self.height, depth=self.depth)
        obj.setBoundingBox(bb)
        # text glyph
        t_glyph = layout.createTextGlyph()
        t_glyph.setId("tglyph_{}".format(self.sid))
        t_glyph.setGraphicalObjectId(self.sid)
        t_glyph.setText(self.text)
        bb = _create_bounding_box(x=self.x, y=self.y, z=self.z, width=self.width, height=self.height, depth=self.depth)
        t_glyph.setBoundingBox(bb)


##########################################################################
# CompartmentGlyph
##########################################################################
class CompartmentGlyph(factory.Sbase):
    def __init__(self, sid, compartment, x, y, z=0, w=200, h=200, d=0, text=None, name=None, sboTerm=None, metaId=None):
        super(CompartmentGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.compartment = compartment
        self.x = x
        self.y = y
        self.z = z
        self.width = w
        self.height = h
        self.depth = d
        self.text = text

    def set_fields(self, obj: libsbml.SpeciesGlyph, layout: libsbml.Layout):
        super(CompartmentGlyph, self).set_fields(obj)
        obj.setCompartmentId(self.compartment)
        bb = _create_bounding_box(x=self.x, y=self.y, z=self.z, width=self.width, height=self.height, depth=self.depth)
        obj.setBoundingBox(bb)
        # text glyph
        t_glyph = layout.createTextGlyph()
        t_glyph.setId("tglyph_{}".format(self.sid))
        t_glyph.setGraphicalObjectId(self.sid)
        t_glyph.setText(self.text)
        bb = _create_bounding_box(x=self.x, y=self.y, z=self.z, width=self.width, height=self.height, dpeth=self.depth)
        t_glyph.setBoundingBox(bb)


##########################################################################
# ReactionGlyph
##########################################################################
class ReactionGlyph(factory.Sbase):

    def __init__(self, sid, reaction, x, y, z=0, species_glyphs=[], w=20, h=20, d=0, text=None, name=None, sboTerm=None, metaId=None):
        super(ReactionGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.reaction = reaction
        self.x = x
        self.y = y
        self.z = z
        self.width = w
        self.height = h
        self.depth = d

        self.text = text
        self.species_glyphs = species_glyphs

        self.layout = None

    def set_fields(self, obj: libsbml.ReactionGlyph, layout: libsbml.Layout):
        super(ReactionGlyph, self).set_fields(obj)
        self.layout = layout
        obj.setReactionId(self.reaction)
        bb = _create_bounding_box(x=self.x, y=self.y, z=self.z, width=self.width, height=self.height, depth=self.depth)
        obj.setBoundingBox(bb)

        # text glyph
        t_glyph = layout.createTextGlyph()
        t_glyph.setId("tglyph_{}".format(self.sid))
        t_glyph.setGraphicalObjectId(self.sid)
        t_glyph.setText(self.text)
        bb = _create_bounding_box(x=self.x, y=self.y, z=self.z, width=0, height=0, depth=0)
        t_glyph.setBoundingBox(bb)

        # get direction of reaction
        eps = 1E-6
        x_tot = 0
        y_tot = 0
        x_r = bb.getX()
        y_r = bb.getY()
        for sg_id, role in self.species_glyphs.items():
            s_glyph = layout.getSpeciesGlyph(sg_id)  # type: libsbml.SpeciesGlyph
            s_bb = s_glyph.getBoundingBox()  # type: libsbml.BoundingBox
            x_s = s_bb.getX()
            y_s = s_bb.getY()
            if role in [LAYOUT_ROLE_SIDESUBSTRATE, LAYOUT_ROLE_SUBSTRATE]:
                x_tot += (x_r - x_s)
                y_tot += (y_r - y_s)
            elif role in [LAYOUT_ROLE_PRODUCT, LAYOUT_ROLE_SIDEPRODUCT]:
                x_tot += (x_s - x_r)
                y_tot += (y_s - y_r)

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
            srg = obj.createSpeciesReferenceGlyph()  # type: libsbml.SpeciesReferenceGlyph
            srg.setId(obj.getId() + "__" + sg_id)
            srg.setSpeciesGlyphId(sg_id)
            srg.setRole(role)

            self._create_curve(layout, srg, obj.getId(), sg_id, role, direction)

    def _create_curve(self, layout: libsbml.Layout, srg: libsbml.SpeciesReferenceGlyph, r_glyph_id, s_glyph_id, role, direction):
        """ Heuristic for creating the curves.

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
        r_glyph = layout.getReactionGlyph(r_glyph_id)  # type: libsbml.ReactionGlyph
        s_glyph = layout.getSpeciesGlyph(s_glyph_id)  # type: libsbml.SpeciesGlyph

        # create curve
        line_segment = srg.createLineSegment()  # type: libsbml.LineSegment

        # calculate start and end points for line
        s_bb = s_glyph.getBoundingBox()  # type: libsbml.BoundingBox
        r_bb = r_glyph.getBoundingBox()  # type: libsbml.BoundingBox

        # dist = 0.2
        dist = 10

        x, y, h, w = r_bb.getX(), r_bb.getY(), r_bb.getHeight(), r_bb.getWidth()
        xs, ys, hs, ws = s_bb.getX(), s_bb.getY(), s_bb.getHeight(), s_bb.getWidth()
        if direction == "right":
            s_point_substrate = (xs+ws, ys+0.5*hs)
            s_point_product = (xs, ys+0.5*hs)
            s_point_modifier = (xs+0.5*ws, y+hs)

            r_point_substrate = (x, y+0.5*h)
            r_point_product = (x+w, y+0.5*h)
            r_point_modifier = (x+0.5*w, y)
        elif direction == "left":
            s_point_substrate = (xs, ys+0.5*hs)
            s_point_product = (xs+ws, ys+0.5*hs)
            s_point_modifier = (xs+0.5*ws, y+hs)

            r_point_substrate = (x+w, y+0.5*h)
            r_point_product = (x, y+0.5*h)
            r_point_modifier = (x + 0.5*w, y)
        elif direction == "down":
            s_point_substrate = (xs+0.5*ws, ys+hs)
            s_point_product = (xs+0.5*ws, ys)
            s_point_modifier = (xs, ys+0.5*hs)

            r_point_substrate = (x+0.5*w, y)
            r_point_product = (x+0.5*w, y+h)
            r_point_modifier = (x+w, y+0.5*h)
        elif direction == "up":
            s_point_substrate = (xs + 0.5 * ws, ys)
            s_point_product = (xs + 0.5 * ws, ys+hs)
            s_point_modifier = (xs, ys + 0.5 * hs)

            r_point_substrate = (x + 0.5 * w, y+h)
            r_point_product = (x + 0.5 * w, y)
            r_point_modifier = (x + w, y + 0.5 * h)

        if role in [LAYOUT_ROLE_ACTIVATOR,
                    LAYOUT_ROLE_INHIBITOR,
                    LAYOUT_ROLE_MODIFIER]:
            # segment from species -> reaction
            line_segment.setStart(s_point_modifier[0], s_point_modifier[1], 0)
            line_segment.setEnd(r_point_modifier[0], r_point_modifier[1], 0)
        elif role in [LAYOUT_ROLE_SUBSTRATE, LAYOUT_ROLE_SIDESUBSTRATE, LAYOUT_ROLE_UNDEFINED]:
            # segment from reaction -> species
            line_segment.setEnd(s_point_substrate[0], s_point_substrate[1], 0)
            line_segment.setStart(r_point_substrate[0], r_point_substrate[1], 0)
        elif role in [LAYOUT_ROLE_PRODUCT, LAYOUT_ROLE_SIDEPRODUCT]:
            # segment from reaction -> species
            line_segment.setEnd(s_point_product[0], s_point_product[1], 0)
            line_segment.setStart(r_point_product[0], r_point_product[1], 0)


def _create_bounding_box(x, y, width, height, z=0, depth=0):
    bb = libsbml.BoundingBox(SBML_LEVEL, SBML_VERSION, LAYOUT_VERSION)  # type: libsbml.BoundingBox
    bb.setX(float(x))
    bb.setY(float(y))
    bb.setZ(float(z))
    bb.setWidth(float(width))
    bb.setHeight(float(height))
    bb.setDepth(float(depth))
    return bb


##########################################################################
# TextGlyph
##########################################################################
