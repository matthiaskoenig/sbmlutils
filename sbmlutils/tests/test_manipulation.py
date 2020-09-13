"""
Test manipulation functions.
"""

from sbmlutils import comp
from sbmlutils import validation
from sbmlutils.manipulation import merge
from sbmlutils.io import write_sbml
from sbmlutils.tests import DATA_DIR


def test_biomodel_merge():
    """ Test model merging.

    Using the pytest tmpdir fixture
    :param tmpdir:
    :return:
    """
    merge_dir = DATA_DIR / 'manipulation' / 'merge'

    # dictionary of ids & paths of models which should be combined
    # here we just bring together the first Biomodels
    model_ids = ["BIOMD000000000{}".format(k) for k in range(1, 5)]
    model_paths = dict(zip(
        model_ids,
        [merge_dir / f"{mid}.xml" for mid in model_ids]
    ))

    # merge model
    out_dir = merge_dir / 'output'
    if not out_dir.exists():
        out_dir.mkdir()

    doc = merge.merge_models(model_paths, out_dir=out_dir,  validate=False)
    assert doc is not None

    Nall, Nerr, Nwarn = validation.check_doc(doc, units_consistency=False)
    assert Nerr == 0
    assert Nwarn == 0
    assert Nall == 0

    # flatten the model
    doc_flat = comp.flatten_sbml_doc(doc)
    assert doc_flat is not None
    write_sbml(doc_flat, filepath=out_dir / "merged_flat.xml")

    Nall, Nerr, Nwarn = validation.check_doc(doc_flat, units_consistency=False)
    assert Nerr == 0
    assert Nwarn in [0, 74]
    assert Nall in [0, 74]
