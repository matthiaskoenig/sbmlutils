# -*- coding=utf-8 -*-
"""
Test model to check the update of global depending parameters in Roadrunner.
Mainly volumes which are calculated based on other parameters.
"""
from __future__ import print_function, division
from libsbml import XMLNode
from sbmlutils.modelcreator import templates
from sbmlutils.modelcreator import modelcreator as mc
from Reactions import *

##############################################################
creators = templates.creators
mid = 'test'
version = 7
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Koenig Test Model</h1>
    <h2>Description</h2>
    <p>Test model.
    </p>
    """ + templates.terms_of_use + """
    </body>
    """)
units = []
compartments = []
species = []
parameters = []
names = []
assignments = []
rules = []
reactions = []

##############################################################
# Compartments
##############################################################
compartments.extend([
    mc.Compartment(sid='ext', value='Vol_e', unit='m3', constant=True, name="external"),
    mc.Compartment(sid='cyto', value='Vol_c', unit='m3', constant=False, name="cytosol"),
    mc.Compartment(sid='pm', value='A_m', unit="m2", constant=True, spatialDimension=2, name="membrane"),
])

##############################################################
# Species
##############################################################
species.extend([
    mc.Species(sid='e__gal', compartment='ext', value=3.0, unit='mM', boundaryCondition=True, name='D-galactose'),
    mc.Species(sid='c__gal', compartment='cyto', value=0.00012, unit='mM', boundaryCondition=False, name='D-galactose'),
])

##############################################################
# Parameters
##############################################################
parameters.extend([
    mc.Parameter(sid='x_cell', value=25E-6, unit='m', constant=True, name="cell diameter"),
    mc.Parameter(sid='Vol_e', value=100E-14, unit='m3', constant=True, name="external volume"),
    mc.Parameter(sid='A_m', value=1.0, unit='m2', constant=True, name="membrane area"),
])

##############################################################
# Assignments
##############################################################
assignments.extend([
    mc.Assignment(sid='Vol_c', value='x_cell*x_cell*x_cell', unit='m3'),
])

##############################################################
# Rules
##############################################################
rules.extend([])

##############################################################
# Reactions
##############################################################
reactions.extend([
    GLUT2_GAL
])
