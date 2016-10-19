"""
Create a comp model.
Test script for working with the comp extension in SBML.

One model composition combines all the kinetic models,
in addition the higher level comp model is created which combines everything (i.e. the FBA & ODE models).
For the simulation of the full combined model the tools have to figure out the subparts which are
simulated with which simulation environment.
"""
from __future__ import print_function
from libsbml import *

import model_factory
from sbmlutils.factory import *
from sbmlutils import comp
import sbmlutils.sbmlio as sbml_io
from simsettings import *


def create_top_level_model(sbml_file):
    """
    Creates the full comp model as combination of FBA and comp models.

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
    sbmlns = SBMLNamespaces(3, 1, "comp", 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    doc.setPackageRequired("fbc", False)

    mdoc = doc.getPlugin("comp")

    # create listOfExternalModelDefinitions
    emd_bounds = comp.create_ExternalModelDefinition(mdoc, "toy_ode_bounds", sbml_file=ode_bounds_file)
    emd_fba = comp.create_ExternalModelDefinition(mdoc, "toy_fba", sbml_file=fba_file)
    emd_update = comp.create_ExternalModelDefinition(mdoc, "toy_ode_update", sbml_file=ode_update_file)
    emd_model = comp.create_ExternalModelDefinition(mdoc, "toy_ode_model", sbml_file=ode_model_file)

    # create models and submodels
    model = doc.createModel()
    model.setId("toy_top_level")
    model.setName("Top level model")
    model_factory.add_generic_info(model)
    mplugin = model.getPlugin("comp")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)

    # add submodel which references the external model definition
    comp.add_submodel_from_emd(mplugin, submodel_sid="bounds", emd=emd_bounds)
    comp.add_submodel_from_emd(mplugin, submodel_sid="fba", emd=emd_fba)
    comp.add_submodel_from_emd(mplugin, submodel_sid="update", emd=emd_update)
    comp.add_submodel_from_emd(mplugin, submodel_sid="model", emd=emd_model)

    # --- compartments ---
    create_compartments(model, [
        {A_ID: "extern", A_NAME: "external compartment", A_VALUE: 1.0, A_SPATIAL_DIMENSION: 3, A_UNIT: model_factory.UNIT_VOLUME},
        {A_ID: 'cell', A_NAME: 'cell', A_VALUE: 1.0, A_SPATIAL_DIMENSION: 3, A_UNIT: model_factory.UNIT_VOLUME}
    ])

    # --- species ---
    # replaced species
    # (fba species are not replaced, because they need their boundaryConditions for the FBA,
    #    and do not depend on the actual concentrations)
    create_species(model, [
        {A_ID: 'C', A_NAME: "C", A_VALUE: 0, A_UNIT: model_factory.UNIT_AMOUNT, A_HAS_ONLY_SUBSTANCE_UNITS: True,
         A_COMPARTMENT: "extern"},
    ])

    # --- parameters ---
    create_parameters(model, [
        # bounds
        {A_ID: 'ub_R1', A_VALUE: 1.0, A_UNIT: model_factory.UNIT_FLUX, A_NAME: 'ub_R1', A_CONSTANT: False},
        {A_ID: "vR3", A_NAME: "vR3 (FBA flux)", A_VALUE: 0.1, A_UNIT: model_factory.UNIT_FLUX, A_CONSTANT: False}
    ])

    # --- reactions ---
    # dummy reaction in top model
    r1 = create_reaction(model, rid="R3", name="R3 dummy", fast=False, reversible=True,
                         reactants={}, products={"C": 1}, compartment="extern")
    # assignment rule
    create_assignment_rules(model, [{A_ID: "vR3", A_VALUE: "R3"}])

    # --- replacements ---
    # replace compartments
    comp.replace_elements(model, 'extern', ref_type=comp.SBASE_REF_TYPE_PORT,
                          replaced_elements={'fba': ['extern_port'], 'update': ['extern_port'], 'model': ['extern_port']})

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
    sbml_io.write_and_check(doc, sbml_file)

###########################################################################################
if __name__ == "__main__":
    import os
    os.chdir(out_dir)

    # create top comp model
    create_top_level_model(top_level_file)

    # flatten the combined model
    from multiscale.sbmlutils import comp
    comp.flattenSBMLFile(top_level_file, output_file=flattened_file)
