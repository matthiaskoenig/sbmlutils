from pathlib import Path
import os
from sbmlutils.comp import flattenSBMLFile
from sbmlutils.report import sbmlreport

from sbmlutils.examples.models.midazolam.model_liver import create_model as create_liver_model
from sbmlutils.examples.models.midazolam.model_kidney import create_model as create_kidney_model
from sbmlutils.examples.models.midazolam.model_intestine import create_model as create_intestine_model
from sbmlutils.examples.models.midazolam.model_body import create_model as create_body_model

if __name__ == "__main__":
    results_path = "./models"

    # create tissue models
    create_intestine_model(results_path)
    create_kidney_model(results_path)
    create_liver_model(results_path)

    # create whole-body model
    [_, _, sbml_path] = create_body_model(results_path)

    print(sbml_path)
    assert os.path.exists(sbml_path)

    sbml_path_flat = "./models/midazolam_body_flat.xml"
    import libsbml
    doc = libsbml.readSBMLFromFile(os.path.abspath(sbml_path))  # type: libsbml.SBMLDocument
    model = doc.getModel()  # type: libsbml.Model


    # FIXME: not working with relative paths
    flattenSBMLFile(os.path.abspath(sbml_path), output_path=os.path.abspath(sbml_path_flat))

    # create model report
    sbmlreport.create_report(sbml_path_flat, "./models/")


