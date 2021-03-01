"""
Test manipulation functions.
"""
from pathlib import Path

import pytest

from sbmlutils import comp, validation
from sbmlutils.io import write_sbml
from sbmlutils.manipulation import merge
from sbmlutils.test import DATA_DIR


@pytest.mark.skip(reason="Model merging currently not working")
def test_biomodel_merge(tmp_path: Path) -> None:
    """Test model merging."""
    merge_dir = DATA_DIR / "manipulation" / "merge"

    # dictionary of ids & paths of models which should be combined
    # here we just bring together the first Biomodels
    model_ids = [f"BIOMD000000000{k}" for k in range(1, 5)]
    model_paths = dict(zip(model_ids, [merge_dir / f"{mid}.xml" for mid in model_ids]))

    # merge model
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    doc = merge.merge_models(model_paths, output_dir=out_dir, validate=False)
    assert doc is not None

    vresults = validation.validate_doc(doc, units_consistency=False)
    assert vresults.error_count == 0
    assert vresults.warning_count == 0
    assert vresults.all_count == 0

    # flatten the model
    doc_flat = comp.flatten_sbml_doc(doc)
    assert doc_flat is not None

    vresults = validation.validate_doc(doc_flat, units_consistency=False)
    assert vresults.error_count == 0
    assert vresults.warning_count in [0, 74]
    assert vresults.all_count in [0, 74]

    merged_sbml_path = out_dir / "merged_flat.xml"
    write_sbml(doc_flat, filepath=merged_sbml_path)
    assert merged_sbml_path.exists()
