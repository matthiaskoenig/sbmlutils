"""
Creates statistics of biomodels.

Models are 31th Biomodels Release
https://www.ebi.ac.uk/biomodels/content/news/biomodels-release-26th-june-2017
"""

import os
import pandas as pd
import libsbml


def get_model_paths(model_folder):
    """Returns list of SBML paths from given folder."""
    paths = []
    for f in os.listdir(model_folder):
        if f.endswith('.xml'):
            f_path = os.path.join(model_folder, f)
            if os.path.isfile(f_path):
                paths.append(f_path)
    return sorted(paths)


def sbml_all_statistics(sbml_paths):
    """ Calculate statistics for all biomodels.

    :return:
    """
    results = []
    index = []
    for path in sbml_paths:
        print(path)
        index.append(os.path.basename(path)[:-4])
        results.append(sbml_statistics(path))

    df = pd.DataFrame(results, index=index)
    return df


def sbml_statistics(sbml_path):
    """Calculate dictionary of statistics for given SBML model

    :param sbml_path:
    :return: dict
    """
    doc = libsbml.readSBMLFromFile(sbml_path)  # type: libsbml.SBMLDocument
    model = doc.getModel()  # type: libsbml.Model
    # core
    s = {
        "level_version": "L{}V{}".format(doc.getLevel(), doc.getVersion())
    }

    if model:
        s["function_definitions"] = model.getNumFunctionDefinitions()
        s["unit_definitions"] = model.getNumUnitDefinitions()
        s["compartments"] = model.getNumCompartments()
        s["species"] = model.getNumSpecies()
        s["parameters"] = model.getNumParameters()
        s["initial_assignments"] = model.getNumInitialAssignments()
        s["rules"] = model.getNumRules()
        s["reactions"] = model.getNumReactions()
        s["constraints"] = model.getNumConstraints()
        s["events"] = model.getNumEvents()

        # kineticLaws & localParameters
        s["kinetic_laws"] = 0
        s["kinetic_laws_math"] = 0
        s["parameters_local"] = 0
        for reaction in model.getListOfReactions():  # type: libsbml.Reaction
            if reaction.isSetKineticLaw():
                s["kinetic_laws"] += 1
                klaw = reaction.getKineticLaw()  # type: libsbml.KineticLaw
                if klaw.isSetMath():
                    # math must be set and cannot be a flux_value

                    # some fbc models abuse kinetic laws via FLUX_VALUE
                    math = klaw.getMath()  # type: libsbml.ASTNode
                    formula = libsbml.formulaToL3String(math)
                    if formula != "FLUX_VALUE":
                        s["kinetic_laws_math"] += 1

                s["parameters_local"] += klaw.getNumParameters()

        # rule details
        s["rules_assignment_rules"] = 0
        s["rules_rate_rules"] = 0
        s["rules_algebraic_rules"] = 0
        for rule in model.getListOfRules():  # type: libsbml.RuleWithVariable
            if rule.isAssignment():
                s["rules_assignment_rules"] += 1
            elif rule.isRate():
                s["rules_rate_rules"] += 1
            elif rule.isAlgebraic():
                s["rules_algebraic_rules"] += 1

        # event details
        s["events_trigger"] = 0
        s["events_priority"] = 0
        s["events_delay"] = 0
        s["events_event_assignments"] = 0

        for event in model.getListOfEvents():  # type: libsbml.Event
            if event.isSetTrigger():
                s["events_trigger"] += 1
            if event.isSetPriority():
                s["events_priority"] += 1
            if event.isSetDelay():
                s["events_delay"] += 1
            s["events_event_assignments"] += event.getNumEventAssignments()
        s["events_math"] = s["events_trigger"] + s["events_priority"] + s["events_delay"] + s["events_event_assignments"]

        s["math"] = s["function_definitions"] + s["initial_assignments"] + s["constraints"] + s["rules"] + s["kinetic_laws_math"] + s["events_math"]

        # FIXME: annotations & SBO terms

    return s


if __name__ == "__main__":

    # directory with all biomodel releases
    biomodels_path = "/home/mkoenig/biomodels"
    for path in sorted(os.walk(biomodels_path)):
        dir = path[0]
        # print(path[0])
        if dir.endswith("/curated") or dir.endswith("/non_curated"):
            print(dir)
            tokens = dir.split("/")
            curation_status = tokens[-1]
            release_date = tokens[-2]
            release, date = release_date.split("_")

            print("*" * 80)
            print(release, date, curation_status)
            print("*" * 80)
            sbml_paths = get_model_paths(dir)
            df = sbml_all_statistics(sbml_paths)
            df["release"] = release
            df["date"] = date
            df["status"] = curation_status

            out_file = "./statistics/{}_{}_{}.tsv".format(release, date, curation_status)
            df.to_csv(out_file, sep="\t")


