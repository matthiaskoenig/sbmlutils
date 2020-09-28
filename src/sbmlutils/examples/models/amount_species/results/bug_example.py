import libsbml
import roadrunner


sbml_path = "body19_livertoy_flat.xml"
r = roadrunner.RoadRunner("body19_livertoy_flat.xml")  # type: roadrunner.RoadRunner
sbml_str = r.getCurrentSBML()

doc1 = libsbml.readSBMLFromFile(sbml_path)  # type: libsbml.SBMLDocument
doc2 = libsbml.readSBMLFromString(sbml_str)  # type: libsbml.SBMLDocument

docs = {"sbml": doc1, "roadrunner": doc2}

for key, doc in docs.items():
    print(key)
    model = doc.getModel()  # type: libsbml.Model
    s = model.getSpecies("Ave_glc")  # type: libsbml.Species
    print(s)
    print("initial concentration: ", s.getInitialConcentration())
    print("initial amount: ", s.getInitialAmount())

    print("-" * 80)
