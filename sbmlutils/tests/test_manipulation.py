from __future__ import print_function

import os
import unittest
from os.path import join as pjoin
from sbmlutils import comp
from sbmlutils import validation

from sbmlutils import manipulation
from sbmlutils.tests.data import data_dir


def test_biomodel_merge():
    manipulation_dir = pjoin(data_dir, 'manipulation')
    cur_dir = os.getcwd()
    os.chdir(manipulation_dir)

    # dictionary of ids & paths of models which should be combined
    # here we just bring together the first Biomodels
    model_ids = ["BIOMD000000000{}".format(k) for k in range(1, 5)]
    model_paths = dict(zip(model_ids, ["{}.xml".format(mid) for mid in model_ids]))
    print(model_paths)

    # merge model
    doc = manipulation.merge_models(model_paths, validate=False)
    assert doc is not None

    Nall, Nerr, Nwarn = validation.check_doc(doc, ucheck=False)
    assert Nerr == 0
    assert Nwarn == 0
    assert Nall == 0

    # flatten the model
    doc_flat = comp.flattenSBMLDocument(doc)
    assert doc_flat is not None

    Nall, Nerr, Nwarn = validation.check_doc(doc_flat, ucheck=False)
    assert Nerr == 0
    # FIXME: bug fixed on next SBML release
    assert Nwarn in [0, 74]
    assert Nall in [0, 74]

    os.chdir(cur_dir)


if __name__ == '__main__':
    unittest.main()
