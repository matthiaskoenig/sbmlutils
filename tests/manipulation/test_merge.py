"""Test model merging functionality."""

import shutil
from pathlib import Path

import libsbml
import pytest

from examples.merge_models.merge_models import merge_models_example
from sbmlutils import comp, validation
from sbmlutils.io import read_sbml, write_sbml
from sbmlutils.manipulation import merge
from sbmlutils.resources import TESTDATA_DIR
from sbmlutils.validation import ValidationOptions


def test_merge_models_example(tmp_path: Path) -> None:
    """Testing the merge model example."""
    merge_models_example(output_dir=tmp_path)


def test_biomodel_merge(tmp_path: Path) -> None:
    """Test model merging."""
    merge_dir = TESTDATA_DIR / "manipulation" / "merge"

    # dictionary of ids & paths of models which should be combined
    # here we just bring together the first Biomodels
    model_ids = [f"BIOMD000000000{k}" for k in range(1, 5)]
    model_paths = dict(
        zip(model_ids, [merge_dir / f"{mid}.xml" for mid in model_ids], strict=False)
    )

    # merge model
    out_dir = tmp_path / "output"
    out_dir.mkdir()

    doc = merge.merge_models(model_paths, output_dir=out_dir)
    assert doc is not None

    vresults = validation.validate_doc(
        doc,
        options=ValidationOptions(units_consistency=False),
    )
    assert vresults.error_count == 0
    assert vresults.warning_count == 0
    assert vresults.all_count == 0

    # flatten the model
    doc_flat = comp.flatten_sbml_doc(doc)
    assert doc_flat is not None

    vresults = validation.validate_doc(
        doc_flat,
        options=ValidationOptions(units_consistency=False),
    )
    assert vresults.error_count == 0
    assert vresults.warning_count in [0, 74]
    assert vresults.all_count in [0, 74]

    merged_sbml_path = out_dir / "merged_flat.xml"
    write_sbml(doc_flat, filepath=merged_sbml_path)
    assert merged_sbml_path.exists()


MERGE_DIR = TESTDATA_DIR / "manipulation" / "merge"


def two_models(model_dir: Path) -> dict[str, Path]:
    """Copy two biomodels into a directory.

    Args:
        model_dir: directory the models are copied to

    Returns:
        the ids of the models and their paths
    """
    model_dir.mkdir(parents=True, exist_ok=True)
    model_paths: dict[str, Path] = {}
    for model_id in ["BIOMD0000000001", "BIOMD0000000002"]:
        model_paths[model_id] = model_dir / f"{model_id}.xml"
        shutil.copy(MERGE_DIR / f"{model_id}.xml", model_paths[model_id])
    return model_paths


def emd_sources(doc: libsbml.SBMLDocument) -> list[str]:
    """Get the sources of the external model definitions of a document.

    Args:
        doc: comp document

    Returns:
        the `comp:source` of every external model definition
    """
    emds = doc.getPlugin("comp").getListOfExternalModelDefinitions()
    return [emds.get(k).getSource() for k in range(emds.size())]


@pytest.mark.parametrize("out_dir", ["out", "sp ace/ü"])
def test_merge_models_relative_paths(forbid_chdir: Path, out_dir: str) -> None:
    """Relative paths are relative to the working directory, which is kept."""
    two_models(forbid_chdir / "models")
    (forbid_chdir / out_dir).mkdir(parents=True)
    model_paths = {
        "BIOMD0000000001": Path("models/BIOMD0000000001.xml"),
        "BIOMD0000000002": Path("models/BIOMD0000000002.xml"),
    }

    doc = merge.merge_models(model_paths, output_dir=Path(out_dir))

    assert Path.cwd() == forbid_chdir
    out_path = forbid_chdir / out_dir
    assert (out_path / "merged.xml").exists()
    assert (out_path / "merged_flat.xml").exists()
    assert emd_sources(doc) == ["BIOMD0000000001_L3.xml", "BIOMD0000000002_L3.xml"]
    assert emd_sources(read_sbml(out_path / "merged.xml")) == emd_sources(doc)
    assert not (out_path / out_dir).exists()


def test_merge_models_str_paths(tmp_path: Path) -> None:
    """Paths given as `str` are accepted like `Path`."""
    model_paths = {mid: str(p) for mid, p in two_models(tmp_path / "models").items()}
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    doc = merge.merge_models(model_paths, output_dir=str(out_dir), flatten=False)

    assert doc is not None
    assert (out_dir / "merged.xml").exists()


def test_merge_models_keeps_model_paths(tmp_path: Path) -> None:
    """The dictionary of the caller is not changed."""
    model_paths = two_models(tmp_path / "models")
    expected = dict(model_paths)

    merge.merge_models(model_paths, output_dir=tmp_path, flatten=False)

    assert model_paths == expected


@pytest.mark.parametrize("sbml_version", [1, 2])
def test_merge_models_level_and_version(tmp_path: Path, sbml_version: int) -> None:
    """The merged model and its external models have the requested version."""
    model_paths = two_models(tmp_path / "models")

    doc = merge.merge_models(
        model_paths, output_dir=tmp_path, flatten=False, sbml_version=sbml_version
    )

    assert (doc.getLevel(), doc.getVersion()) == (3, sbml_version)
    for path in [tmp_path / "merged.xml", tmp_path / "BIOMD0000000001_L3.xml"]:
        doc_written = read_sbml(path)
        assert (doc_written.getLevel(), doc_written.getVersion()) == (3, sbml_version)


def test_merge_models_unconvertible_model(tmp_path: Path) -> None:
    """A model which cannot be converted to the requested version raises."""
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    model.setId("rate_of")
    k: libsbml.Parameter = model.createParameter()
    k.setId("k")
    k.setValue(1.0)
    k.setConstant(True)
    x: libsbml.Parameter = model.createParameter()
    x.setId("x")
    x.setValue(1.0)
    x.setConstant(False)
    rule: libsbml.RateRule = model.createRateRule()
    rule.setVariable("x")
    rule.setMath(libsbml.parseL3Formula("rateOf(k)"))
    path = tmp_path / "rate_of.xml"
    write_sbml(doc, filepath=path)

    with pytest.raises(ValueError, match="cannot be converted to SBML L3V1"):
        merge.merge_models({"rate_of": path}, output_dir=tmp_path, flatten=False)


@pytest.mark.parametrize(("sbml_level", "sbml_version"), [(2, 4), (3, 3)])
def test_merge_models_unsupported_level_and_version(
    tmp_path: Path, sbml_level: int, sbml_version: int
) -> None:
    """Only SBML L3V1 and L3V2 can hold a comp model."""
    with pytest.raises(ValueError, match="SBML L3V1 or L3V2"):
        merge.merge_models(
            two_models(tmp_path / "models"),
            output_dir=tmp_path,
            sbml_level=sbml_level,
            sbml_version=sbml_version,
        )


def test_merge_models_ids_differ_from_model_ids(tmp_path: Path) -> None:
    """The ids of the external models need not be the ids of their models."""
    model_paths = two_models(tmp_path / "models")
    renamed = {"first": model_paths["BIOMD0000000001"]}
    renamed["second"] = model_paths["BIOMD0000000002"]

    doc = merge.merge_models(renamed, output_dir=tmp_path)

    vresults = validation.validate_doc(
        doc, options=ValidationOptions(units_consistency=False)
    )
    assert vresults.error_count == 0
    assert (tmp_path / "merged_flat.xml").exists()


@pytest.mark.parametrize("out_dir", ["out", "sp ace/ü"])
def test_merge_models_submodel_sbo_term(tmp_path: Path, out_dir: str) -> None:
    """A submodel has the SBO term of the model it instantiates."""
    model_paths = two_models(tmp_path / "models")
    doc = read_sbml(model_paths["BIOMD0000000001"])
    doc.getModel().setSBOTerm("SBO:0000062")
    write_sbml(doc, filepath=model_paths["BIOMD0000000001"])
    (tmp_path / out_dir).mkdir(parents=True)

    merged_doc = merge.merge_models(
        model_paths, output_dir=tmp_path / out_dir, flatten=False
    )

    comp_model: libsbml.CompModelPlugin = merged_doc.getModel().getPlugin("comp")
    assert comp_model.getSubmodel("BIOMD0000000001").getSBOTermID() == "SBO:0000062"
    assert not comp_model.getSubmodel("BIOMD0000000002").isSetSBOTerm()
