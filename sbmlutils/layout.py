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


##########################################################################
# Layout
##########################################################################
class Layout(factory.Sbase):

    def __init__(self, sid, width, height, species_glyphs, reaction_glyphs, name=None, sboTerm=None, metaId=None):
        """ Create a layout. """
        super(Layout, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.width = width
        self.height = height
        self.species_glyphs = species_glyphs
        self.reaction_glyphs = reaction_glyphs

    def create_sbml(self, model: libsbml.Model):
        # doc = model.getSBMLDocument()  # type: libsbml.SBMLDocument
        layout_model = doc.getPlugin("layout")  # type: libsbml.LayoutModelPlugin
        layout = layout_model.createLayout()  # type: libsbml.Layout
        self.set_fields(layout)

        # TODO: species_glyphs -> SpeciesGlyphs & TextGlyphs
        # TODO: reaction_glyphs -> ReactionGlyphs & ReactionGlyphs

        return layout

    def set_fields(self, obj: libsbml.Layout):
        super(Layout, self).set_fields(obj)
        obj.setWidth(self.width)
        obj.setHeight(self.height)


##########################################################################
# SpeciesGlyph
##########################################################################
class SpeciesGlyph(factory.Sbase):
    def __init__(self, layout, sid, species, x, y, width=200, height=50, text=None, name=None, sboTerm=None, metaId=None):
        """ Create an ExternalModelDefinitions.
        """
        super(SpeciesGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.layout = layout  # type: libsbml.Layout
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
    def __init__(self, layout, sid, reaction, x, y, species_glyphs=[], width=200, height=50, text=None, name=None, sboTerm=None, metaId=None):
        """ Create an ExternalModelDefinitions.
        """
        super(ReactionGlyph, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.layout = layout  # type: libsbml.Layout
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