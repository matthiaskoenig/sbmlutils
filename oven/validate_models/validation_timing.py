from __future__ import absolute_import, print_function

import libsbml
import time

model_paths = ["ecoli_top.xml", "RECON1.xml"]


def timing():
    doc = libsbml.SBMLDocument()
    model = doc.createModel()
    c_id = "c"
    c = model.createCompartment()
    c.setId(c_id)
    c.setVolume(1.0)
    N_species = 100
    for k in range(N_species):
        s = model.createSpecies()
        s.setId("s{}".format(k))
        s.setInitialConcentration(1.0)
        s.setConstant(True)
        t_start = time.time()
        doc.checkConsistency()
        t_check = time.time()
        print('{}, {}'.format(k, t_check - t_start))


def validation_example():
    for p in model_paths:
        for with_units in [False, True]:
            t_start = time.time()
            print("\n*** {} ***".format(p))
            doc = libsbml.readSBMLFromFile(p)
            t_read = time.time()
            print('reading: {:.3} [s]'.format(t_read - t_start))

            doc.setConsistencyChecks(libsbml.LIBSBML_CAT_UNITS_CONSISTENCY, with_units)
            doc.checkConsistency()
            t_check = time.time()
            print('checkConsistency (units={}): {:.3} [s]'.format(with_units, t_check - t_read))


if __name__ == "__main__":
    timing()
