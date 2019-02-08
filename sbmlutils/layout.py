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


##########################################################################
# Layout
##########################################################################
class Layout(factory.Sbase):

    def __init__(self, sid, width, height, species_glyphs, reaction_glyphs, name=None, sboTerm=None, metaId=None):
        """ Create a layout. """
        super(Layout, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.width = float(width)
        self.height = float(height)
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

        # TODO: species_glyphs -> SpeciesGlyphs & TextGlyphs
        # TODO: reaction_glyphs -> ReactionGlyphs & ReactionGlyphs

        return layout

    def set_fields(self, obj: libsbml.Layout):
        super(Layout, self).set_fields(obj)
        dim = libsbml.Dimensions(SBML_LEVEL, SBML_VERSION, LAYOUT_VERSION)  # type: libsbml.Dimensions
        dim.setWidth(self.width)
        dim.setHeight(self.height)
        obj.setDimensions(dim)


##########################################################################
# SpeciesGlyph
##########################################################################
class SpeciesGlyph(factory.Sbase):
    def __init__(self, sid, species, x, y, width=200, height=50, text=None, name=None, sboTerm=None, metaId=None):
        """ Create an ExternalModelDefinitions.
        """
        super(SpeciesGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.species = species
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text


##########################################################################
# ReactionGlyph
##########################################################################
class ReactionGlyph(factory.Sbase):
    def __init__(self, sid, reaction, x, y, species_glyphs=[], width=200, height=50, text=None, name=None, sboTerm=None, metaId=None):
        """ Create an ExternalModelDefinitions.
        """
        super(ReactionGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.reaction = reaction
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.species_glyphs = species_glyphs
        self.text = text


##########################################################################
# TextGlyph
##########################################################################