from __future__ import absolute_import, print_function

import libsbml
import time

model_paths = ["ecoli_top.xml", "RECON1.xml"]

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