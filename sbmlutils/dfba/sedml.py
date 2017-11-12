"""
Helper functions to create SED-ML.
"""
import os
import phrasedml


def create_sedml(sedml_location, sbml_location, directory, dt, tend, species_ids, reaction_ids):
    """ Creates SED-ML file for the given simulation.

    :param sedml_location:
    :param sbml_location:
    :param directory:
    :param dt:
    :param tend:
    :return:
    """
    phrasedml.setWorkingDirectory(directory)
    steps = int(1.0 * tend / dt)

    p = """
          model1 = model "{}"
          sim1 = simulate uniform(0, {}, {})
          sim1.algorithm = kisao.500
          task1 = run sim1 on model1
          plot "Figure 1: DFBA species vs. time" time vs {}
          plot "Figure 2: DFBA fluxes vs. time" time vs {}
          report "Report 1: DFBA species vs. time" time vs {}
          report "Report 2: DFBA fluxes vs. time" time vs {}

    """.format(sbml_location, tend, steps, species_ids, reaction_ids, species_ids, reaction_ids)

    return_code = phrasedml.convertString(p)
    if return_code is None:
        print(phrasedml.getLastError())

    sedml = phrasedml.getLastSEDML()
    # print(sedml)

    sedml_file = os.path.join(directory, sedml_location)
    with open(sedml_file, "w") as f:
        f.write(sedml)
    print(sedml_file)
