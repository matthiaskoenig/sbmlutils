"""Tests for flattening a comp model from its file."""

import os
import shutil
from pathlib import Path

import libsbml
import pytest

from sbmlutils.comp import flatten_sbml
from sbmlutils.io import read_sbml
from sbmlutils.resources import COMP_ICG_BODY, COMP_ICG_LIVER


def forbid_chdir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail the test as soon as anything changes the working directory.

    The working directory is global to the process, a library function which
    changes it breaks every other thread of the process.

    Args:
        monkeypatch: the fixture which undoes the patch after the test
    """

    def chdir(path: str | os.PathLike[str]) -> None:
        """Refuse to change the working directory."""
        raise AssertionError(f"working directory changed to '{path}'")

    monkeypatch.setattr(os, "chdir", chdir)


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


@pytest.mark.parametrize("liver_dir", ["", "liver"])
def test_flatten_sbml_relative_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, liver_dir: str
) -> None:
    """A relative input and output path are relative to the working directory."""
    write_icg_body(tmp_path / "models", liver_dir=liver_dir)
    monkeypatch.chdir(tmp_path)
    forbid_chdir(monkeypatch)

    doc = flatten_sbml(Path("models/icg_body.xml"), Path("flat/icg_body_flat.xml"))

    assert Path.cwd() == tmp_path
    assert (tmp_path / "flat" / "icg_body_flat.xml").exists()
    assert not (tmp_path / "models" / "flat").exists()
    doc_flat = read_sbml(tmp_path / "flat" / "icg_body_flat.xml")
    assert doc_flat.getModel().getNumSpecies() == doc.getModel().getNumSpecies() > 0


def test_flatten_sbml_str_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Paths given as `str` are accepted like `Path`."""
    write_icg_body(tmp_path / "models")
    monkeypatch.chdir(tmp_path)
    forbid_chdir(monkeypatch)

    flatten_sbml("models/icg_body.xml", "icg_body_flat.xml")

    assert (tmp_path / "icg_body_flat.xml").exists()


def test_flatten_sbml_error_keeps_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A model which cannot be flattened raises and leaves the working directory."""
    body_path = write_icg_body(tmp_path / "models")
    (body_path.parent / "icg_liver.xml").unlink()
    monkeypatch.chdir(tmp_path)
    forbid_chdir(monkeypatch)

    with pytest.raises(ValueError, match="could not be flattend"):
        flatten_sbml(Path("models/icg_body.xml"), Path("icg_body_flat.xml"))

    assert Path.cwd() == tmp_path
    assert not (tmp_path / "icg_body_flat.xml").exists()


def test_read_sbml_location_is_absolute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A document read from a relative path resolves its external definitions."""
    write_icg_body(tmp_path / "models", liver_dir="liver")
    monkeypatch.chdir(tmp_path)

    doc = read_sbml(Path("models/icg_body.xml"))

    assert doc.getLocationURI() == (tmp_path / "models" / "icg_body.xml").as_uri()
    emd: libsbml.ExternalModelDefinition = (
        doc.getPlugin("comp").getListOfExternalModelDefinitions().get(0)
    )
    assert emd.getReferencedModel() is not None
