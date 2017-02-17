"""
Create diauxic comp model.
Test script for working with the comp extension in SBML.

One model composition combines all the kinetic models,
in addition the higher level comp model is created which combines everything (i.e. the FBA & ODE models).
For the simulation of the full combined model the tools have to figure out the subparts which are
simulated with which simulation environment.
"""
from __future__ import print_function
from libsbml import *

import model_factory
from sbmlutils import factory as mc
from sbmlutils import comp
import sbmlutils.sbmlio as sbml_io
from dgsettings import comp_file, flattened_file, update_file, bounds_file, fba_file


def create_top_level_model(sbml_file, directory):
    """
    Creates the full comp model as combination of FBA and comp models.

    The submodels must already exist in the given directory

    connections
    ------------
    [1] flux bounds
    kinetic reaction bounds => replace the FBA bounds
    comp_ode.submodel_bounds__ub_R1 => fba_R1.upper_bound

    [2] reaction rates (fluxes)
    FBA flux (all reactions) => replaces Reaction flux in kinetic model

    ** FBA **
    <listOfParameters>
        <parameter id="ub_R1" name="ub R1" value="1" units="item_per_s" constant="false"/>
        <parameter id="lb" name="lower bound" value="0" units="item_per_s" constant="true"/>
        <parameter id="ub" name="upper bound" value="1000" units="item_per_s" constant="true"/>
        <parameter id="v_R1" name="R1 flux" value="0" units="item_per_s" constant="false"/>
        <parameter id="v_R2" name="R2 flux" value="0" units="item_per_s" constant="false"/>
        <parameter id="v_R3" name="R3 flux" value="0" units="item_per_s" constant="false"/>
    </listOfParameters>
    """
    working_dir = os.getcwd()
    os.chdir(directory)
    sbmlns = SBMLNamespaces(3, 1, "comp", 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    doc.setPackageRequired("fbc", False)

    mdoc = doc.getPlugin("comp")

    # create listOfExternalModelDefinitions
    emd_fba = comp.create_ExternalModelDefinition(mdoc, "diauxic_fba", sbml_file=fba_file)
    emd_bounds = comp.create_ExternalModelDefinition(mdoc, "diauxic_bounds", sbml_file=bounds_file)
    emd_update = comp.create_ExternalModelDefinition(mdoc, "diauxic_update", sbml_file=update_file)

    # create models and submodels
    model = doc.createModel()
    model.setId("diauxic_comp")
    model.setName("Top level model")
    model_factory.add_generic_info(model)
    mplugin = model.getPlugin("comp")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)

    # add submodel which references the external model definition
    comp.add_submodel_from_emd(mplugin, submodel_sid="bounds", emd=emd_bounds)
    comp.add_submodel_from_emd(mplugin, submodel_sid="fba", emd=emd_fba)
    comp.add_submodel_from_emd(mplugin, submodel_sid="update", emd=emd_update)

    # Compartments
    mc.create_objects(model, [
        mc.Compartment(sid='bioreactor', value=1.0, unit='l', constant=True, name='bioreactor',
                       spatialDimension=3),
    ])

    # Species
    # replaced species
    # (fba species are not replaced, because they need their boundaryConditions for the FBA,
    #    and do not depend on the actual concentrations)
    mc.create_objects(model, [
        # internal
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='Ac', name="acetate", value=0.4, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        mc.Species(sid='O2', name="oxygen", value=0.21, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='X', name="biomass", value=0.001, unit='g_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        # dummy species for dummy reactions
        mc.Species(sid='S_dummy', name="S_dummy", value=0, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
    ])

    # Parameters
    mc.create_objects(model, [
        # bounds
        mc.Parameter(sid="ub_vGlcxt", name="ub vGlcxt", value=10.0, unit=UNIT_FLUX, constant=False),

        # fluxes from fba
        mc.Parameter(sid="vGlcxt", name="vGlcxt (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        mc.Parameter(sid="vAc", name="vAc (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        mc.Parameter(sid="vO2", name="vO2 (FBA flux)", value=1.0, constant=True, unit="mmol_per_hg"),
        mc.Parameter(sid="vX", name="vX (FBA flux)", value=1.0, constant=True, unit="g_per_lh"),

    ])

    # Reactions
    # dummy reaction in top model
    mc.create_reaction(model, rid="dummy_vGlcxt", name="vGlcxt dummy", reversible=False,
                       reactants={}, products={"S_dummy": 1}, compartment="bioreactor")
    mc.create_reaction(model, rid="dummy_vO2", name="vO2 dummy", reversible=False,
                       reactants={}, products={"S_dummy": 1}, compartment="bioreactor")
    mc.create_reaction(model, rid="dummy_vAc", name="vAc dummy", reversible=False,
                       reactants={}, products={"S_dummy": 1}, compartment="bioreactor")
    mc.create_reaction(model, rid="dummy_vX", name="vX dummy", reversible=False,
                       reactants={}, products={"S_dummy": 1}, compartment="bioreactor")
    # AssignmentRules
    mc.create_objects(model, [
        mc.AssignmentRule(sid="vGlcxt", value="dummy_vGlcxt"),
        mc.AssignmentRule(sid="vAc", value="dummy_vAc"),
        mc.AssignmentRule(sid="vO2", value="dummy_vO2"),
        mc.AssignmentRule(sid="vX", value="dummy_vX"),
    ])


    # --- replacements ---

    # compartments
    comp.replace_elements(model, 'bioreactor', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['bioreactor_port'],
                                             'update': ['bioreactor_port'],
                                             'bounds': ['bioreactor_port']})

    # replace species
    comp.replace_elements(model, 'Glcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['Glcxt_port'],
                                             'update': ['Glcxt_port'],
                                             'bounds': ['Glcxt_port']})
    comp.replace_elements(model, 'O2', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['O2_port'],
                                             'update': ['O2_port']})
    comp.replace_elements(model, 'Ac', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['Ac_port'],
                                             'update': ['Ac_port']})
    comp.replace_elements(model, 'X', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['X_port'],
                                             'update': ['X_port']})
    # bounds
    comp.replace_elements(model, 'ub_vGlcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'bounds': ['ub_vGlcxt_port'], 'fba': ['ub_vGlcxt_port']})
    # fluxes
    comp.replace_elements(model, 'vGlcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['vGlcxt_port']})
    comp.replace_elements(model, 'vAc', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['vAc_port']})
    comp.replace_elements(model, 'vO2', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['vO2_port']})
    comp.replace_elements(model, 'vX', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'update': ['vX_port']})


    # FBA: replace reaction by fba reaction
    comp.replaced_by(model, 'dummy_vGlcxt', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="vGlcxt_port")
    comp.replaced_by(model, 'dummy_vAc', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="vAc_port")
    comp.replaced_by(model, 'dummy_vO2', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="vO2_port")
    comp.replaced_by(model, 'dummy_vX', ref_type=comp.SBASE_REF_TYPE_PORT,
                     submodel='fba', replaced_by="vX_port")

    # replace units
    # TODO
    # for uid in ['s', 'kg', 'm3', 'm2', 'mM', 'item_per_m3', 'm', 'per_s', 'item_per_s']:
    #    comp.replace_element_in_submodels(model, uid, ref_type=comp.SBASE_REF_TYPE_UNIT,
    #                                      submodels=['bounds', 'fba', 'update', 'ode'])

    # write SBML file
    sbml_io.write_and_check(doc, os.path.join(directory, sbml_file))

    # flatten the combined model
    comp.flattenSBMLFile(sbml_file=os.path.join(directory, top_level_file),
                         output_file=os.path.join(directory, flattened_file))

    # change back the working dir
    os.chdir(working_dir)


###########################################################################################
if __name__ == "__main__":

    # create top comp model
    from dgsettings import out_dir, comp_file
    create_top_level_model(comp_file, out_dir)


