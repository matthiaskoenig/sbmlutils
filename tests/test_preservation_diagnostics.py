"""Known parser losses remain visible through parse, merge, and write."""

from pathlib import Path

import libsbml
import pytest

from sbmlutils.factory import Model, create_model
from sbmlutils.parser import sbml_to_model
from sbmlutils.validation import PreservationError

CORE = "http://www.sbml.org/sbml/level3/version2/core"
GROUPS = "http://www.sbml.org/sbml/level3/version1/groups/version1"
LAYOUT = "http://www.sbml.org/sbml/level3/version1/layout/version1"


def groups_source(count: int = 1) -> str:
    """A supported core model carrying valid groups content."""
    groups = "".join(
        f'<groups:group groups:id="g{i}" groups:kind="collection"/>'
        for i in range(count)
    )
    return (
        f'<sbml xmlns="{CORE}" xmlns:groups="{GROUPS}" level="3" version="2" '
        'groups:required="false"><model id="m"><groups:listOfGroups>'
        f"{groups}</groups:listOfGroups></model></sbml>"
    )


def test_group_loss_retained_through_write(tmp_path: Path) -> None:
    """Grouped source losses are available separately from construction."""
    model = sbml_to_model(groups_source(25))
    assert len(model.preservation_diagnostics) == 1
    loss = model.preservation_diagnostics[0]
    assert loss.code == "unsupported_package_content"
    assert loss.count == 25
    assert loss.example == "group(g0)"
    result = create_model(model, tmp_path / "m.xml", sbml_version=2, validate=False)
    assert result.preservation_diagnostics == model.preservation_diagnostics
    assert result.diagnostics == ()
    assert "listOfGroups" not in result.sbml_path.read_text(encoding="utf-8")


def test_strict_parse_and_write(tmp_path: Path) -> None:
    """Strict checks reject known loss and preserve an existing destination."""
    path = tmp_path / "source.xml"
    source = groups_source()
    path.write_text(source, encoding="utf-8")
    with pytest.raises(PreservationError) as caught:
        sbml_to_model(path, strict_preservation=True)
    assert caught.value.diagnostics[0].code == "unsupported_package_content"
    model = sbml_to_model(path)
    with pytest.raises(PreservationError):
        create_model(model, path, strict_preservation=True, create_antimony=True)
    assert path.read_text(encoding="utf-8") == source
    assert not path.with_suffix(".ant").exists()


def test_empty_package_and_core_control(tmp_path: Path) -> None:
    """An empty unsupported declaration is not a content loss."""
    model = sbml_to_model(groups_source(0), strict_preservation=True)
    assert model.preservation_diagnostics == ()
    result = create_model(
        model,
        tmp_path / "core.xml",
        sbml_version=2,
        strict_preservation=True,
        strict=True,
        raise_on_error=True,
    )
    assert result.validation is not None
    assert result.validation.is_valid()


def test_model_history() -> None:
    """A creator and timestamps are reported rather than silently omitted."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.setId("m")
    model.setMetaId("meta_m")
    history = libsbml.ModelHistory()
    creator = libsbml.ModelCreator()
    creator.setFamilyName("Example")
    creator.setGivenName("Author")
    history.addCreator(creator)
    date = libsbml.Date("2026-01-01T00:00:00Z")
    history.setCreatedDate(date)
    history.setModifiedDate(date)
    assert model.setModelHistory(history) == libsbml.LIBSBML_OPERATION_SUCCESS
    parsed = sbml_to_model(libsbml.writeSBMLToString(doc))
    assert any(d.code == "model_history" for d in parsed.preservation_diagnostics)


def test_layout_loss() -> None:
    """Layout content is detected even though the factory can author layouts."""
    source = (
        f'<sbml xmlns="{CORE}" xmlns:layout="{LAYOUT}" level="3" version="2" '
        'layout:required="false"><model id="m"><layout:listOfLayouts>'
        '<layout:layout layout:id="l"><layout:dimensions layout:width="1" '
        'layout:height="1" layout:depth="1"/></layout:layout>'
        "</layout:listOfLayouts></model></sbml>"
    )
    with pytest.raises(PreservationError) as caught:
        sbml_to_model(source, strict_preservation=True)
    assert any("layout" in d.message for d in caught.value.diagnostics)


def test_custom_annotation_and_document_metadata() -> None:
    """Non-RDF annotations and document-level metadata have explicit findings."""
    source = (
        f'<sbml xmlns="{CORE}" level="3" version="2" metaid="document_meta">'
        '<model id="m"><annotation><custom:data xmlns:custom="urn:example">'
        "keep me</custom:data></annotation></model></sbml>"
    )
    model = sbml_to_model(source)
    assert {d.code for d in model.preservation_diagnostics} == {
        "document_metadata",
        "custom_annotation",
    }
    clean = sbml_to_model(
        f'<sbml xmlns="{CORE}" level="3" version="2"><model id="m"/></sbml>'
    )
    assert clean.preservation_diagnostics == ()


def test_merged_findings_survive_clean_last_input(tmp_path: Path) -> None:
    """A later input cannot erase an earlier source's preservation findings."""
    parsed = sbml_to_model(groups_source())
    merged = Model.merge_models([parsed, Model("clean")])
    assert merged.preservation_diagnostics == parsed.preservation_diagnostics
    with pytest.raises(PreservationError):
        create_model(
            [parsed, Model("clean")], tmp_path / "m.xml", strict_preservation=True
        )
    assert not (tmp_path / "m.xml").exists()


def test_fbc_association_metadata() -> None:
    """Metadata on an association node is not represented by its infix string."""
    ns = libsbml.SBMLNamespaces(3, 2)
    ns.addPackageNamespace("fbc", 3)
    doc = libsbml.SBMLDocument(ns)
    doc.setPackageRequired("fbc", False)
    model = doc.createModel()
    model.setId("m")
    model.getPlugin("fbc").setStrict(False)
    gene = model.getPlugin("fbc").createGeneProduct()
    gene.setId("g")
    gene.setLabel("g")
    reaction = model.createReaction()
    reaction.setId("r")
    reaction.setReversible(False)
    association = reaction.getPlugin("fbc").createGeneProductAssociation()
    node = association.createGeneProductRef()
    node.setGeneProduct("g")
    node.setMetaId("node_metadata")
    parsed = sbml_to_model(libsbml.writeSBMLToString(doc))
    loss = next(
        d for d in parsed.preservation_diagnostics if d.code == "association_metadata"
    )
    assert loss.count == 1
    assert "node_metadata" in (loss.example or "")


def test_reserved_math_symbol() -> None:
    """A MathML identifier which becomes ambiguous in infix is reported."""
    doc = libsbml.SBMLDocument(3, 2)
    model = doc.createModel()
    model.setId("m")
    parameter = model.createParameter()
    parameter.setId("pi")
    parameter.setConstant(False)
    rule = model.createAssignmentRule()
    rule.setVariable("pi")
    name = libsbml.ASTNode(libsbml.AST_NAME)
    name.setName("pi")
    rule.setMath(name)
    parsed = sbml_to_model(libsbml.writeSBMLToString(doc))
    assert any(
        d.code == "ambiguous_math_symbol" for d in parsed.preservation_diagnostics
    )
