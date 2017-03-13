# -*- coding=utf-8 -*-
"""
This module creates the sub-models and combined comp model for the toy model.

The toy model consists hereby of
- a FBA submodels
- deterministic ODE models
- and stochastic ODE models

The SBML comp extension is used for hierarchical model composition, i.e. to create
the main model and the kinetic model parts.
"""
from __future__ import print_function
from libsbml import *
# FIXME: no wildcard import
import toysettings


from os.path import join as pjoin

import sbmlutils.annotation as sbml_annotation
import model_factory
from sbmlutils import factory as mc
from sbmlutils import comp
import sbmlutils.sbmlio as sbml_io
from sbmlutils.report import sbmlreport
from sbmlutils.dfba.builder import LOWER_BOUND_DEFAULT, UPPER_BOUND_DEFAULT

XMLOutputStream.setWriteTimestamp(False)

# FIXME: write down the information on how to generate DFBA models from
#   given FBA models
#   - add dynamic species (which are the dynamic species? This should be
#     the external one which are changed via the exchange reactions.
#     This are NOT the same species like the internal species in the FBA

########################################################################
# General model information
########################################################################
version = 2
DT_SIM = 0.1
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Wholecell Toy Model</h1>
    <h2>Description</h2>
    <p>This is a toy model for coupling models with different modeling frameworks via comp.</p>

    <div class="dc:publisher">This file has been produced by
      <a href="https://livermetabolism.com/contact.html" title="Matthias Koenig" target="_blank">Matthias Koenig</a>.
      </div>

    <h2>Terms of use</h2>
      <div class="dc:rightsHolder">Copyright © 2017 Matthias Koenig</div>
      <div class="dc:license">
      <p>Redistribution and use of any part of this model, with or without modification, are permitted provided that
      the following conditions are met:
        <ol>
          <li>Redistributions of this SBML file must retain the above copyright notice, this list of conditions
              and the following disclaimer.</li>
          <li>Redistributions in a different form must reproduce the above copyright notice, this list of
              conditions and the following disclaimer in the documentation and/or other materials provided
          with the distribution.</li>
        </ol>
        This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
             the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.</p>
      </div>
    </body>
""")
creators = [
    mc.Creator(familyName='Koenig', givenName='Matthias', email='konigmatt@googlemail.com',
               organization='Humboldt University Berlin', site='http://livermetabolism.com')
]
main_units = {
    'time': 's',
    'extent': UNIT_KIND_ITEM,
    'substance': UNIT_KIND_ITEM,
    'length': 'm',
    'area': 'm2',
    'volume': 'm3',
}
units = [
    mc.Unit('s', [(UNIT_KIND_SECOND, 1.0)]),
    mc.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('m3', [(UNIT_KIND_METRE, 3.0)]),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0, 0),
                   (UNIT_KIND_METRE, -3.0)]),
    mc.Unit('per_s', [(UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('item_per_s', [(UNIT_KIND_ITEM, 1.0),
                           (UNIT_KIND_SECOND, -1.0)]),
    mc.Unit('item_per_m3', [(UNIT_KIND_ITEM, 1.0),
                            (UNIT_KIND_METRE, -3.0)]),
]

UNIT_TIME = 's'
UNIT_AMOUNT = UNIT_KIND_ITEM
UNIT_AREA = 'm2'
UNIT_VOLUME = 'm3'
UNIT_CONCENTRATION = 'item_per_m3'
UNIT_FLUX = 'item_per_s'


def add_generic_info(model):
    """ Adds the shared information to the models.

    :param model: SBMLModel instance
    :return:
    """
    sbml_annotation.set_model_history(model, creators)
    mc.create_objects(model, units)
    mc.set_main_units(model, main_units)
    model.setNotes(notes)


####################################################
# FBA submodel
####################################################
def fba_model(sbml_file, directory):
    """
    Create the fba model.
    FBA submodel in FBC v2 which uses parameters as flux bounds.
    """
    sbmlns = SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("fbc", 2)
    sbmlns.addPackageNamespace("comp", 1)

    doc_fba = SBMLDocument(sbmlns)
    doc_fba.setPackageRequired("comp", True)
    mdoc = doc_fba.getPlugin("comp")
    doc_fba.setPackageRequired("fbc", False)
    model = doc_fba.createModel()
    mplugin = model.getPlugin("fbc")
    mplugin.setStrict(True)

    # model
    model.setId('toy_fba')
    model.setName('toy (FBA submodel)')
    model.setSBOTerm(comp.SBO_FLUX_BALANCE_FRAMEWORK)
    add_generic_info(model)

    # Compartments
    compartments = [
        mc.Compartment(sid='extern', value=1.0, unit=UNIT_VOLUME, constant=True, name='external compartment', spatialDimension=3),
        mc.Compartment(sid='cell', value=1.0, unit=UNIT_VOLUME, constant=True, name='cell', spatialDimension=3),
        mc.Compartment(sid='membrane', value=1.0, unit=UNIT_AREA, constant=True, name='membrane', spatialDimension=2),
    ]
    mc.create_objects(model, compartments)

    # Species
    species = [
        # external
        mc.Species(sid='A', name="A", value=10, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern"),
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern"),
        # internal
        mc.Species(sid='B1', name="B1", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="cell"),
        mc.Species(sid='B2', name="B2", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="cell"),
    ]
    mc.create_objects(model, species)

    parameters = [
        # bounds
        mc.Parameter(sid="ub_R1", name="ub R1", value=1.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="lb", name="lower bound", value=0.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub", name="upper bound", value=1000.0, unit=UNIT_FLUX, constant=True),
        # exchange bounds
        mc.Parameter(sid="ub_EX_A", value=1000.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="lb_EX_A", value=-1000.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub_EX_C", value=1000.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="lb_EX_C", value=-1000.0, unit=UNIT_FLUX, constant=True),
    ]
    mc.create_objects(model, parameters)

    # reactions with constant flux
    r1 = mc.create_reaction(model, rid="R1", name="A import (R1)", fast=False, reversible=True,
                            reactants={"A": 1}, products={"B1": 1}, compartment='membrane')
    r2 = mc.create_reaction(model, rid="R2", name="B1 <-> B2 (R2)", fast=False, reversible=True,
                            reactants={"B1": 1}, products={"B2": 1}, compartment='cell')
    r3 = mc.create_reaction(model, rid="R3", name="B2 export (R3)", fast=False, reversible=True,
                            reactants={"B2": 1}, products={"C": 1}, compartment='membrane')

    # exchange reactions
    r_EX_A = mc.create_reaction(model, rid="EX_A", reversible=True,
                            reactants={"A": 1}, products={}, compartment='membrane')
    r_EX_C = mc.create_reaction(model, rid="EX_C", reversible=True,
                                reactants={"C": 1}, products={}, compartment='membrane')

    # flux bounds
    mc.set_flux_bounds(r1, lb="lb", ub="ub_R1")
    mc.set_flux_bounds(r2, lb="lb", ub="ub")
    mc.set_flux_bounds(r3, lb="lb", ub="ub")
    # exchange bounds
    mc.set_flux_bounds(r_EX_A, lb="lb_EX_A", ub="ub_EX_A")
    mc.set_flux_bounds(r_EX_C, lb="lb_EX_C", ub="ub_EX_C")

    # objective function
    mc.create_objective(mplugin, oid="R3_maximize", otype="maximize",
                        fluxObjectives={"R3": 1.0}, active=True)

    # create ports
    # comp._create_port(model, pid="R3_port", idRef="R3", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_R1_port", idRef="ub_R1", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_A_port", idRef="lb_EX_A", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_A_port", idRef="ub_EX_A", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_C_port", idRef="lb_EX_C", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_C_port", idRef="ub_EX_C", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_sbml(doc_fba, filepath=os.path.join(directory, sbml_file), validate=True)

####################################################
# BOUNDS submodel
####################################################
def bounds_model(sbml_file, directory):
    """"
    Submodel for dynamically calculating the flux bounds.
    The dynamically changing flux bounds are the input to the
    FBA model.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    model = doc.createModel()
    model.setId("toy_bounds")
    model.setName("toy (BOUNDS calculation submodel)")

    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    objects = [
        # definition of min and max
        mc.Function('max', 'lambda(x,y, piecewise(x,gt(x,y),y) )', name='minimum of arguments'),
        mc.Function('min', 'lambda(x,y, piecewise(x,lt(x,y),y) )', name='maximum of arguments'),

        mc.Compartment(sid='extern', value=1.0, unit=UNIT_VOLUME, constant=True, name='external compartment',
                       spatialDimension=3),

        # species
        mc.Species(sid='A', name="A", value=10, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern"),
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern"),

        # dt parameter
        mc.Parameter(sid='dt', value=0.1, unit=UNIT_TIME, constant=True),
        # exchange bounds
        mc.Parameter(sid="lb_default", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub_EX_A", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="lb_EX_A", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub_EX_C", value=UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="lb_EX_C", value=LOWER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True),

        # kinetic bound parameter
        mc.Parameter(sid='ub_R1', value=1.0, unit=UNIT_FLUX, constant=False, sboTerm="SBO:0000346"),
        mc.Parameter(sid='k1', value=-0.2, unit="per_s", name="k1", constant=False),


        # rate rules
        mc.RateRule(sid="ub_R1", value="k1*ub_R1"),

        # bounds assignment rules
        # FIXME: guidelines bound depending if species is in amount or concentration

        mc.AssignmentRule(sid="lb_EX_A", value='max(lb_default, -A/dt)'),
        mc.AssignmentRule(sid="lb_EX_C", value='max(lb_default, -C/dt)'),
    ]
    mc.create_objects(model, objects)

    # FIXME: guidelines list ports for bounds model (dt, species, compartments, bounds)
    # FIXME: guidelines move ReplacedElements to TOP model definition
    # ports
    # dt, species and compartments
    comp._create_port(model, pid="dt_port", idRef="dt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="A_port", idRef="A", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="C_port", idRef="C", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="extern_port", idRef="extern", portType=comp.PORT_TYPE_PORT)

    # bounds
    comp._create_port(model, pid="ub_R1_port", idRef="ub_R1", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_A_port", idRef="lb_EX_A", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_A_port", idRef="ub_EX_A", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="lb_EX_C_port", idRef="lb_EX_C", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_EX_C_port", idRef="ub_EX_C", portType=comp.PORT_TYPE_PORT)

    sbml_io.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)

####################################################
# UPDATE submodel
####################################################
def update_model(sbml_file, directory):
    """
        Submodel for dynamically updating the metabolite count.
        This updates the ode model based on the FBA fluxes.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    model = doc.createModel()
    model.setId("toy_update")
    model.setName("toy (metabolite UPDATE submodel)")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    objects = [
        # FIXME: guidelines add compartments for species
        mc.Compartment(sid='extern', value=1.0, unit="m3", constant=True, name='external compartment', spatialDimension=3),

        mc.Species(sid='A', name="A", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True, compartment="extern"),
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True, compartment="extern"),

        # FIXME: guidelines add SBOTerm & add info for parameters
        mc.Parameter(sid="EX_A", value=1.0, constant=False, unit=UNIT_FLUX),
        mc.Parameter(sid="EX_C", value=1.0, constant=False, unit=UNIT_FLUX),
    ]
    mc.create_objects(model, objects)

    # exchange reactions
    r_EX_A = mc.create_reaction(model, rid="update_A", reversible=True,
                                reactants={"A": 1}, products={},
                                formula="-EX_A", sboTerm="SBO:0000631")
    r_EX_C = mc.create_reaction(model, rid="update_C", reversible=True,
                                reactants={"C": 1}, products={},
                                formula="-EX_C", sboTerm="SBO:0000631")

    # FIXME: guidelines describe ports
    comp._create_port(model, pid="extern_port", idRef="extern", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="A_port", idRef="A", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="C_port", idRef="C", portType=comp.PORT_TYPE_PORT)

    # FIXME: describe how the EX_* parameters get their values
    comp._create_port(model, pid="EX_A_port", idRef="EX_A", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="EX_C_port", idRef="EX_C", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)

####################################################
# TOP submodel
####################################################
def top_model(sbml_file, directory, emds):
    """ Create top comp model.

    Creates full comp model by combining fba, update and bounds
    model with additional kinetics in the top model.
    """
    working_dir = os.getcwd()
    os.chdir(directory)
    sbmlns = SBMLNamespaces(3, 1, "comp", 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    doc.setPackageRequired("fbc", False)

    mdoc = doc.getPlugin("comp")

    # create listOfExternalModelDefinitions
    emd_bounds = comp.create_ExternalModelDefinition(mdoc, "toy_bounds", source=emds["toy_bounds"])
    emd_fba = comp.create_ExternalModelDefinition(mdoc, "toy_fba", source=emds["toy_fba"])
    emd_update = comp.create_ExternalModelDefinition(mdoc, "toy_update", source=emds["toy_update"])

    # create models and submodels
    model = doc.createModel()
    model.setId("toy_top")
    model.setName("toy (TOP model)")
    model_factory.add_generic_info(model)
    mplugin = model.getPlugin("comp")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)

    # add submodel which references the external model definition
    comp.add_submodel_from_emd(mplugin, submodel_id="bounds", emd=emd_bounds)
    comp.add_submodel_from_emd(mplugin, submodel_id="fba", emd=emd_fba)
    comp.add_submodel_from_emd(mplugin, submodel_id="update", emd=emd_update)

    # Compartments
    mc.create_objects(model, [
        mc.Compartment(sid="extern", name="external compartment", value=1.0, constant=True,
                       spatialDimension=3, unit=model_factory.UNIT_VOLUME),
        mc.Compartment(sid='cell', name='cell', value=1.0, constant=True,
                       spatialDimension=3, unit=model_factory.UNIT_VOLUME),

        mc.Species(sid='C', name="C", value=0, unit=model_factory.UNIT_AMOUNT,
                   hasOnlySubstanceUnits=True, compartment="extern"),

        # bounds

        mc.Parameter(sid="vR3", name="vR3 (FBA flux)", value=0.1, unit=model_factory.UNIT_FLUX, constant=False),

        # kinetic
        mc.Parameter(sid="k_R4", name="k R4", value=0.1, constant=True, unit="per_s"),
    ])

    # Reactions
    # dummy reaction in top model
    mc.create_reaction(model, rid="R3", name="R3 dummy", fast=False, reversible=True,
                       reactants={}, products={"C": 1}, compartment="extern")
    # kinetic reaction (MMK)
    mc.create_reaction(model, rid="R4", name="C -> D", fast=False, reversible=False,
                       reactants={"C": 1}, products={"D": 1}, formula="k_R4*C", compartment="extern")

    # AssignmentRules
    mc.create_objects(model, [
        mc.AssignmentRule(sid="vR3", value="R3"),
    ])



    # --- replacements ---
    # replace compartments
    comp.replace_elements(model, 'extern', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['extern_port'], 'update': ['extern_port'],
                                             'model': ['extern_port']})

    comp.replace_elements(model, 'cell', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['cell_port']})

    # replace parameters
    comp.replace_elements(model, 'ub_R1', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'bounds': ['ub_R1_port'], 'fba': ['ub_R1_port']})
    comp.replace_elements(model, 'vR3', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['vR3_port']})

    # replace species
    comp.replace_elements(model, 'C', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['C_port'], 'update': ['C_port'],
                                             'model': ['C_port']})

    # replace reaction by fba reaction
    comp.replaced_by(model, 'R3', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="R3_port")

    # replace units
    for uid in ['s', 'kg', 'm3', 'm2', 'mM', 'item_per_m3', 'm', 'per_s', 'item_per_s']:
        comp.replace_element_in_submodels(model, uid, ref_type=comp.SBASE_REF_TYPE_UNIT,
                                          submodels=['bounds', 'fba', 'update', 'model'])

    # write SBML file
    sbml_io.write_sbml(doc, filepath=os.path.join(directory, sbml_file), validate=True)

    # change back the working dir
    os.chdir(working_dir)


def create_model(out_dir):
    """ Create all submodels and comp model.

    :return:
    """
    if out_dir is None:
        out_dir = toysettings.out_dir

    directory = pjoin(out_dir, 'v{}'.format(version))
    if not os.path.exists(directory):
        print('Create directory: {}'.format(directory))
        os.mkdir(directory)

    # create sbml
    fba_model(toysettings.fba_file, directory)
    bounds_model(toysettings.bounds_file, directory)
    update_model(toysettings.update_file, directory)

    emds = {
        "toy_fba": toysettings.fba_file,
        "toy_bounds": toysettings.bounds_file,
        "toy_update": toysettings.update_file,
    }

    # flatten top model
    top_model(toysettings.top_file, directory, emds)
    comp.flattenSBMLFile(sbml_path=pjoin(directory, toysettings.top_file),
                         output_path=pjoin(directory, toysettings.flattened_file))
    # create reports
    sbml_paths = [pjoin(directory, fname) for fname in
                  # [fba_file, bounds_file, update_file, top_file, flattened_file]]
                  [toysettings.fba_file,
                   toysettings.bounds_file,
                   toysettings.update_file,
                   toysettings.top_file,
                   toysettings.flattened_file]]
    sbmlreport.create_sbml_reports(sbml_paths, directory, validate=False)

########################################################################################################################
if __name__ == "__main__":
    create_model()
