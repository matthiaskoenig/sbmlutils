# -*- coding=utf-8 -*-
"""
Script for adding ports and interfaces to the RBC model.
"""
try:
    import libsbml
    from libsbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE
except ImportError:
    import tesbml as libsbml
    from tesbml import XMLNode, UNIT_KIND_METRE, UNIT_KIND_SECOND, UNIT_KIND_LITRE, UNIT_KIND_GRAM, UNIT_KIND_MOLE

from sbmlutils.modelcreator import templates
import sbmlutils.factory as mc
import sbmlutils.comp as mcomp
from sbmlutils.modelcreator.processes import ReactionTemplate

PORT_SUFFIX = "_port"

import os
path_dir = os.path.dirname(os.path.realpath(__file__))
version = 1
MODEL_PATH = os.path.join(path_dir, "./input/dutoit3_mmol_compartments_v5.xml")


########################################################################################################################
# RBC Metabolism
########################################################################################################################
def prepare_rbc_model(model_path, name, target_dir):
    """ Add ports to the RBC model.

    :param model_path:
    :param name:
    :param target_dir:
    :return:
    """
    doc = libsbml.readSBMLFromFile(model_path)  # type: libsbml.SBMLDocument

    # add comp package
    # sbmlns = libsbml.SBMLNamespaces(doc.getLevel(), doc.getVersion())
    # sbmlns.addPackageNamespace("comp", 1)
    doc.enablePackage("http://www.sbml.org/sbml/level3/version1/comp/version1", "comp", True)
    # doc.setNamespaces(sbmlns)
    doc.setPackageRequired("comp", True)

    model = doc.getModel()
    model.setId(name)
    print(model)
    cmodel = model.getPlugin("comp")  # type: libsbml.CompModelPlugin

    def create_port(sid):
        """" Creates port for given SBase ID."""
        p = cmodel.createPort()  # type: libsbml.Port
        port_sid = f'{sid}{PORT_SUFFIX}'
        p.setId(port_sid)
        p.setName(port_sid)
        p.setMetaId(port_sid)
        p.setSBOTerm(599)  # port
        p.setIdRef(sid)
        return p

    # add ports
    cmodel = model.getPlugin("comp")  # type: libsbml.CompModelPlugin
    for sid in ['Vplasma', 'glcEXT', 'lacEXT', 'phosEXT', 'pyrEXT']:
        create_port(sid)

    output_path = os.path.join(target_dir, "{}.xml".format(name))
    libsbml.writeSBMLToFile(doc, output_path)
    return output_path


if __name__ == "__main__":
    from sbmlutils.report import sbmlreport
    if False:
        sbmlreport.create_sbml_report(MODEL_PATH, out_dir=os.path.join(path_dir, "./input/"))

    target_dir = os.path.join(path_dir, './model/')
    name = 'rbc_parasite_model'
    output_path = prepare_rbc_model(model_path=MODEL_PATH, name=name, target_dir=target_dir)
    sbmlreport.create_sbml_report(output_path, out_dir=os.path.join(path_dir, "./model/"))
