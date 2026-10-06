"""Driving a model through a comp model with interpolated data."""

from pathlib import Path

import libsbml
import numpy as np
import pandas as pd
import pytest
from interpolation_models import uptake_model, write_model

from sbmlutils.comp import flatten_sbml
from sbmlutils.data.interpolation import Interpolation
from sbmlutils.factory import InitialAssignment

TIMECOURSE = pd.DataFrame(
    {
        "time": [0.0, 2.0, 4.0, 6.0],
        "glc_ext": [5.0, 8.0, 6.0, 5.0],
        "f": [1.0, 2.0, 0.5, 1.0],
        "ext": [2.0, 2.5, 2.0, 1.5],
    }
)


def _interpolation(*columns: str) -> Interpolation:
    """The linear interpolation of the time course, x and the columns."""
    return Interpolation(TIMECOURSE[["time", *columns]], method="linear")


def _errors(doc: libsbml.SBMLDocument) -> list[str]:
    """The errors of a full consistency check of a document."""
    doc.checkConsistency()
    return [
        doc.getError(k).getMessage()
        for k in range(doc.getNumErrors())
        if doc.getError(k).getSeverity() >= libsbml.LIBSBML_SEV_ERROR
    ]


def _flat_id(flat: libsbml.Model, sid: str) -> str:
    """The id of an element of the original in the flattened model."""
    return sid if flat.getElementBySId(sid) is not None else f"uptake__{sid}"


def test_external_reference(tmp_path: Path) -> None:
    """The original is referenced relative to the comp file and is untouched."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    original = path.read_bytes()
    doc = _interpolation("glc_ext").drive_comp(path, filepath=tmp_path / "driven.xml")
    assert path.read_bytes() == original
    assert (tmp_path / "driven.xml").exists()
    emd = doc.getPlugin("comp").getExternalModelDefinition("uptake")
    assert emd.getSource() == "uptake.xml"
    assert emd.getModelRef() == "uptake"
    top = doc.getModel()
    assert top.getId() == "uptake_driven"
    assert top.getPlugin("comp").getSubmodel("uptake").getModelRef() == "uptake"
    assert _errors(doc) == []


def test_external_reference_in_other_directory(tmp_path: Path) -> None:
    """The source is relative to the directory of the comp file."""
    path = write_model(uptake_model(), tmp_path / "models" / "uptake.xml")
    out = tmp_path / "out" / "driven.xml"
    out.parent.mkdir()
    doc = _interpolation("f").drive_comp(path, filepath=out)
    emd = doc.getPlugin("comp").getExternalModelDefinition("uptake")
    assert emd.getSource() == "../models/uptake.xml"
    flat = flatten_sbml(out, tmp_path / "flat.xml")
    assert flat.getModel().getAssignmentRuleByVariable("f") is not None


def test_absolute_reference_without_filepath(tmp_path: Path) -> None:
    """Without a file the source is absolute and the document checks."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    doc = _interpolation("f").drive_comp(path)
    emd = doc.getPlugin("comp").getExternalModelDefinition("uptake")
    assert Path(emd.getSource()) == path.resolve()
    assert _errors(doc) == []


def test_embed(tmp_path: Path) -> None:
    """`embed=True` copies the original in, also from a string or a document."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    for source in (path, path.read_text(), libsbml.readSBMLFromFile(str(path))):
        doc = _interpolation("f").drive_comp(source, embed=True)
        plugin = doc.getPlugin("comp")
        assert plugin.getNumExternalModelDefinitions() == 0
        assert plugin.getModelDefinition("uptake").getNumReactions() == 2
        assert _errors(doc) == []


def test_string_without_embed_raises(tmp_path: Path) -> None:
    """A string or a document has no file to reference."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    with pytest.raises(ValueError, match="embed=True"):
        _interpolation("f").drive_comp(path.read_text())


def test_species_target_placeholders(tmp_path: Path) -> None:
    """A species is replaced by a species, its compartment by the original's."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    top = _interpolation("glc_ext").drive_comp(path).getModel()
    species = top.getSpecies("glc_ext")
    assert species.getBoundaryCondition()
    assert not species.getConstant()
    replaced = species.getPlugin("comp").getReplacedElement(0)
    assert (replaced.getSubmodelRef(), replaced.getIdRef()) == ("uptake", "glc_ext")
    compartment = top.getCompartment("ext")
    replaced_by = compartment.getPlugin("comp").getReplacedBy()
    assert (replaced_by.getSubmodelRef(), replaced_by.getIdRef()) == ("uptake", "ext")


def test_reference_through_port(tmp_path: Path) -> None:
    """An element with a port of the original is referenced by its port."""
    model = uptake_model()
    model.parameters[1].port = True
    path = write_model(model, tmp_path / "uptake.xml")
    top = _interpolation("f").drive_comp(path).getModel()
    replaced = top.getParameter("f").getPlugin("comp").getReplacedElement(0)
    assert replaced.getPortRef() == "f_port"


def test_initial_assignment_with_metaid_is_deleted(tmp_path: Path) -> None:
    """An initial assignment with a metaid is deleted from the submodel."""
    model = uptake_model()
    model.assignments = [InitialAssignment("f", "2 * k", metaId="meta_ia_f")]
    path = write_model(model, tmp_path / "uptake.xml")
    doc = _interpolation("f").drive_comp(path)
    submodel = doc.getModel().getPlugin("comp").getSubmodel("uptake")
    assert submodel.getDeletion(0).getMetaIdRef() == "meta_ia_f"
    assert _errors(doc) == []


def test_initial_assignment_without_metaid_raises(tmp_path: Path) -> None:
    """Without a metaid the initial assignment cannot be deleted."""
    model = uptake_model()
    model.assignments = [InitialAssignment("f", "2 * k")]
    path = write_model(model, tmp_path / "uptake.xml")
    doc = libsbml.readSBMLFromFile(str(path))
    doc.getModel().getInitialAssignmentBySymbol("f").unsetMetaId()
    libsbml.writeSBMLToFile(doc, str(path))
    with pytest.raises(ValueError, match="`drive`"):
        _interpolation("f").drive_comp(path)


def test_level_2_raises(tmp_path: Path) -> None:
    """Comp is a Level 3 package."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml", level=2, version=4)
    with pytest.raises(ValueError, match="Level 3"):
        _interpolation("f").drive_comp(path)


def test_embedding_hierarchical_model_raises(tmp_path: Path) -> None:
    """A model with comp content is referenced, not embedded."""
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    driven = tmp_path / "driven.xml"
    _interpolation("f").drive_comp(path, filepath=driven)
    with pytest.raises(ValueError, match="hierarchical"):
        _interpolation("glc_ext").drive_comp(driven, embed=True)


SCENARIOS: dict[str, tuple[pd.DataFrame, dict[str, str] | None]] = {
    "parameter": (TIMECOURSE[["time", "f"]], None),
    "species": (TIMECOURSE[["time", "glc_ext"]], None),
    "compartment": (TIMECOURSE[["time", "ext"]], None),
    "species in driven compartment": (TIMECOURSE[["time", "glc_ext", "ext"]], None),
    "model quantity as x": (
        pd.DataFrame({"f": [0.0, 1.0, 2.0], "rate": [0.0, 0.25, 1.0]}),
        {"rate": "k"},
    ),
}


@pytest.mark.parametrize("scenario", SCENARIOS)
@pytest.mark.parametrize("embed", [False, True])
def test_comp_equals_in_place(tmp_path: Path, scenario: str, embed: bool) -> None:
    """The flattened comp model simulates as the model driven in place."""
    roadrunner = pytest.importorskip("roadrunner")
    data, targets = SCENARIOS[scenario]
    interpolation = Interpolation(data, method="linear")
    path = write_model(uptake_model(), tmp_path / "uptake.xml")
    in_place = tmp_path / "in_place.xml"
    interpolation.drive(path, targets, filepath=in_place)
    comp = tmp_path / "comp.xml"
    doc = interpolation.drive_comp(path, targets, filepath=comp, embed=embed)
    assert _errors(doc) == []
    flat = tmp_path / "flat.xml"
    flat_model = flatten_sbml(comp, flat).getModel()

    r_in_place = roadrunner.RoadRunner(str(in_place))
    r_flat = roadrunner.RoadRunner(str(flat))
    ids = ["glc", "glc_ext", "ext", "f", "k"]
    s_in_place = r_in_place.simulate(0, 6, 13, selections=["time", *ids])
    s_flat = r_flat.simulate(
        0, 6, 13, selections=["time", *[_flat_id(flat_model, sid) for sid in ids]]
    )
    np.testing.assert_allclose(s_flat, s_in_place, rtol=1e-6, atol=1e-9)
