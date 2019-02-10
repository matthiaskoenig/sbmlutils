"""
Utilities for the creation and work with layout models.
"""

from __future__ import print_function, division, absolute_import

import os
import warnings
import logging
import time
from sbmlutils.logutils import bcolors

try:
    import libsbml
except ImportError:
    import tesbml as libsbml

import sbmlutils.factory as factory
import sbmlutils.validation as validation
from sbmlutils.validation import check

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
    def __init__(self, sid, species, x, y, z=0, width=50, height=20, depth=0, text=None, name=None, sboTerm=None, metaId=None):
        super(SpeciesGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.species = species
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.height = height
        self.depth = depth
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
    def __init__(self, sid, compartment, x, y, z=0, width=200, height=200, depth=0, text=None, name=None, sboTerm=None, metaId=None):
        super(CompartmentGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.compartment = compartment
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.height = height
        self.depth = depth
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
    def __init__(self, sid, reaction, x, y, z=0, species_glyphs=[], width=20, height=20, depth=0, text=None, name=None, sboTerm=None, metaId=None):
        super(ReactionGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.reaction = reaction
        self.x = x
        self.y = y
        self.z = z
        self.width = width
        self.height = height
        self.depth = depth

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
        bb = _create_bounding_box(x=self.x, y=self.y, z=self.z, width=self.width, height=self.height, depth=self.depth)
        t_glyph.setBoundingBox(bb)

        # create speciesReferenceGlyphs
        for sg_id, role in self.species_glyphs.items():
            srg = obj.createSpeciesReferenceGlyph()  # type: libsbml.SpeciesReferenceGlyph
            srg.setId(obj.getId() + "__" + sg_id)
            srg.setSpeciesGlyphId(sg_id)
            srg.setRole(role)

            self._create_curve(layout, obj.getId(), sg_id, role)

    def _create_curve(self, layout: libsbml.Layout, r_glyph_id, s_glyph_id, role):

        r_glyph = layout.getReactionGlyph(r_glyph_id)  # type: libsbml.ReactionGlyph
        s_glyph = layout.getSpeciesGlyph(s_glyph_id)  # type: libsbml.SpeciesGlyph

        # create curve
        line_segment = r_glyph.createLineSegment()  # type: libsbml.LineSegment

        # calculate start and end points for line
        s_bb = s_glyph.getBoundingBox()  # type: libsbml.BoundingBox
        r_bb = r_glyph.getBoundingBox()  # type: libsbml.BoundingBox

        dist = 0.2
        if s_bb.getX() <= r_bb.getX():
            x_start = s_bb.getX() + (1 + dist) * s_bb.getWidth()
            x_end = r_bb.getX() - dist * s_bb.getWidth()
        else:
            x_start = s_bb.getX() - dist * s_bb.getWidth()
            x_end = r_bb.getX() + (1+dist) * s_bb.getWidth()

        if s_bb.getY() <= r_bb.getY():
            y_start = s_bb.getY() + (1 + dist) * s_bb.getHeight()
            y_end = r_bb.getY() - dist * s_bb.getHeight()
        else:
            y_start = s_bb.getY() - dist * s_bb.getHeight()
            y_end = r_bb.getY() + (1 + dist) * s_bb.getHeight()

        if s_bb.getZ() <= r_bb.getZ():
            z_start = s_bb.getZ() + (1 + dist) * s_bb.getDepth()
            z_end = r_bb.getZ() - dist * s_bb.getDepth()
        else:
            z_start = s_bb.getZ() - dist * s_bb.getDepth()
            z_end = r_bb.getZ() + (1 + dist) * s_bb.getDepth()

        # direction of line
        if role in [LAYOUT_ROLE_SUBSTRATE,
                    LAYOUT_ROLE_SIDESUBSTRATE,
                    LAYOUT_ROLE_ACTIVATOR,
                    LAYOUT_ROLE_INHIBITOR,
                    LAYOUT_ROLE_MODIFIER,
                    LAYOUT_ROLE_UNDEFINED]:
            # segment from species -> reaction
            line_segment.setStart(x_start, y_start, z_start)
            line_segment.setEnd(x_end, y_end, z_end)
        else:
            # segment from reaction -> species
            line_segment.setStart(x_end, y_end, z_end)
            line_segment.setEnd(x_start, y_start, z_start)


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