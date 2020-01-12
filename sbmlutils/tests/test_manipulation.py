"""
Test manipulation functions.
"""
import os
import libsbml

from sbmlutils import comp
from sbmlutils import validation
from sbmlutils import manipulation
from sbmlutils.tests.data import data_dir


def test_biomodel_merge():
    """ Test model merging.

    Using the pytest tmpdir fixture
    :param tmpdir:
    :return:
    """
    merge_dir = os.path.join(data_dir, 'manipulation', 'merge')

    # dictionary of ids & paths of models which should be combined
    # here we just bring together the first Biomodels
    model_ids = ["BIOMD000000000{}".format(k) for k in range(1, 5)]
    model_paths = dict(zip(model_ids,
                           [os.path.join(merge_dir, "{}.xml".format(mid)) for mid in model_ids])
                       )
    print(model_paths)

    # merge model
    out_dir = os.path.join(merge_dir, 'output')
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    print('out_dir:', out_dir)

    doc = manipulation.merge_models(model_paths, out_dir=out_dir,  validate=False)
    assert doc is not None

    Nall, Nerr, Nwarn = validation.check_doc(doc, units_consistency=False)
    assert Nerr == 0
    assert Nwarn == 0
    assert Nall == 0

    # flatten the model
    doc_flat = comp.flattenSBMLDocument(doc)
    assert doc_flat is not None
    libsbml.writeSBMLToFile(doc_flat, os.path.join(out_dir, "merged_flat.xml"))

    Nall, Nerr, Nwarn = validation.check_doc(doc_flat, units_consistency=False)
    assert Nerr == 0
    assert Nwarn in [0, 74]
    assert Nall in [0, 74]
