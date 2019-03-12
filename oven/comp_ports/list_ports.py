"""
Example using libsbml to list the ports in a comp model.
"""
import os
import libsbml


def list_ports(model_path):
    """

    :param model_path: path to sbml model
    :return:
    """
    """ List the ports in the given model.

    :return:
    """
    if not os.path.exists(model_path):
        raise IOError("SBML path does not exist.")

    doc = libsbml.readSBMLFromFile(model_path)  # type: libsbml.SBMLDocument
    model = doc.getModel()  # type: libsbml.Model
    model_comp = model.getPlugin("comp")  # type: libsbml.CompModelPlugin
    print(model_comp)
    for port in model_comp.getListOfPorts():  # type: libsbml.Port
        print("\tPort: ",
              port.getId(),
              port.getMetaId(),
              port.getIdRef(),
              port.getMetaIdRef(),
              port.getUnitRef(),
              port.getPortRef())


if __name__ == "__main__":
    list_ports(model_path="./apap_body_3.xml")

