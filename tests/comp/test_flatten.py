"""Tests for flattening a comp model from its file."""

import shutil
import sys
from pathlib import Path

import libsbml
import pytest

from sbmlutils.comp import flatten_sbml
from sbmlutils.io import read_sbml
from sbmlutils.resources import COMP_ICG_BODY, COMP_ICG_LIVER


def write_icg_body(model_dir: Path, liver_dir: str = "") -> Path:
    """Write the icg body model with its external liver model into a directory.

    Args:
        model_dir: directory the body model is written to
        liver_dir: directory of the liver model relative to `model_dir`, empty
            for the same directory

    Returns:
        path of the body model
    """
    liver_path = model_dir / liver_dir / "icg_liver.xml"
    liver_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(COMP_ICG_LIVER, liver_path)

    source = f"{liver_dir}/icg_liver.xml" if liver_dir else "icg_liver.xml"
    body = COMP_ICG_BODY.read_text()
    assert 'comp:source="icg_liver.xml"' in body
    body_path = model_dir / "icg_body.xml"
    body_path.write_text(
        body.replace('comp:source="icg_liver.xml"', f'comp:source="{source}"')
    )
    return body_path


#: libsbml opens the file of an external model definition itself, with the
#: narrow (ANSI) file API on Windows, which cannot open a non-ASCII path
NON_ASCII_EXTERNAL_ON_WINDOWS = pytest.mark.xfail(
    sys.platform == "win32",
    reason="libsbml cannot open an external model definition in a non-ASCII "
    "directory on Windows",
    strict=True,
)

#: directories of the model relative to the working directory: a plain one, one
#: with a space, which a file URI percent-encodes, and one with a non-ASCII
#: character
MODEL_DIRS = [
    "models",
    "sp ace",
    pytest.param("ü", marks=NON_ASCII_EXTERNAL_ON_WINDOWS),
]


@pytest.mark.parametrize("model_dir", MODEL_DIRS)
@pytest.mark.parametrize("liver_dir", ["", "liver"])
def test_flatten_sbml_relative_paths(
    forbid_chdir: Path, model_dir: str, liver_dir: str
) -> None:
    """A relative input and output path are relative to the working directory."""
    write_icg_body(forbid_chdir / model_dir, liver_dir=liver_dir)

    doc = flatten_sbml(Path(model_dir, "icg_body.xml"), Path("flat/icg_body_flat.xml"))

    assert Path.cwd() == forbid_chdir
    flat_path = forbid_chdir / "flat" / "icg_body_flat.xml"
    assert flat_path.exists()
    assert not (forbid_chdir / model_dir / "flat").exists()
    doc_flat = read_sbml(flat_path)
    assert doc_flat.getModel().getNumSpecies() == doc.getModel().getNumSpecies() > 0


@pytest.mark.parametrize("model_dir", MODEL_DIRS)
def test_flatten_sbml_absolute_paths(tmp_path: Path, model_dir: str) -> None:
    """An absolute path is flattened wherever the working directory is."""
    body_path = write_icg_body(tmp_path / model_dir, liver_dir="liver")

    flatten_sbml(body_path, tmp_path / model_dir / "icg_body_flat.xml")

    assert (tmp_path / model_dir / "icg_body_flat.xml").exists()


#: a comp model whose submodel instantiates a model definition of the same
#: document, so flattening it opens no other file
_SBML_COMP_INTERNAL = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
    'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" '
    'level="3" version="2" comp:required="true">'
    '<model id="top"><comp:listOfSubmodels>'
    '<comp:submodel comp:id="sub" comp:modelRef="md"/>'
    "</comp:listOfSubmodels></model>"
    "<comp:listOfModelDefinitions>"
    '<comp:modelDefinition id="md"><listOfParameters>'
    '<parameter id="k" value="1" constant="true"/>'
    "</listOfParameters></comp:modelDefinition>"
    "</comp:listOfModelDefinitions></sbml>"
)


@pytest.mark.parametrize("model_dir", ["sp ace", "ü"])
def test_flatten_sbml_without_external_definitions(
    tmp_path: Path, model_dir: str
) -> None:
    """A model which names no other file is flattened in any directory.

    The files are read and written by python, so a non-ASCII directory works
    on every platform as long as libsbml has no external file to open.
    """
    sbml_path = tmp_path / model_dir / "top.xml"
    sbml_path.parent.mkdir(parents=True)
    sbml_path.write_text(_SBML_COMP_INTERNAL, encoding="utf-8")
    flat_path = tmp_path / model_dir / "top_flat.xml"

    flatten_sbml(sbml_path, flat_path)

    model: libsbml.Model = read_sbml(flat_path).getModel()
    assert model.getNumParameters() == 1
    assert model.getParameter(0).getId() == "sub__k"


def test_flatten_sbml_str_paths(forbid_chdir: Path) -> None:
    """Paths given as `str` are accepted like `Path`."""
    write_icg_body(forbid_chdir / "models")

    flatten_sbml("models/icg_body.xml", "icg_body_flat.xml")

    assert (forbid_chdir / "icg_body_flat.xml").exists()


def test_flatten_sbml_error_keeps_working_directory(forbid_chdir: Path) -> None:
    """A model which cannot be flattened raises and leaves the working directory."""
    body_path = write_icg_body(forbid_chdir / "models")
    (body_path.parent / "icg_liver.xml").unlink()

    with pytest.raises(ValueError, match="could not be flattend"):
        flatten_sbml(Path("models/icg_body.xml"), Path("icg_body_flat.xml"))

    assert Path.cwd() == forbid_chdir
    assert not (forbid_chdir / "icg_body_flat.xml").exists()


@pytest.mark.parametrize("model_dir", MODEL_DIRS)
def test_read_sbml_resolves_external_definitions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, model_dir: str
) -> None:
    """A document read from a relative path resolves its external definitions."""
    write_icg_body(tmp_path / model_dir, liver_dir="liver")
    monkeypatch.chdir(tmp_path)

    doc = read_sbml(Path(model_dir, "icg_body.xml"))

    emd: libsbml.ExternalModelDefinition = (
        doc.getPlugin("comp").getListOfExternalModelDefinitions().get(0)
    )
    assert emd.getReferencedModel() is not None


def test_flatten_sbml_raises_for_a_comp_library(tmp_path: Path) -> None:
    """A document with only model definitions has no model to flatten into."""
    sbml_path = tmp_path / "library.xml"
    sbml_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" '
        'xmlns:comp="http://www.sbml.org/sbml/level3/version1/comp/version1" '
        'level="3" version="2" comp:required="true">'
        "<comp:listOfModelDefinitions>"
        '<comp:modelDefinition id="md"/>'
        "</comp:listOfModelDefinitions>"
        "</sbml>"
    )
    with pytest.raises(ValueError, match="without a model cannot be flattened"):
        flatten_sbml(sbml_path, sbml_flat_path=tmp_path / "flat.xml")
