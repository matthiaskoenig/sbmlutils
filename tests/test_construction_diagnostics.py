"""Construction findings must describe input losses, independent of validation."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import libsbml
import pytest

from sbmlutils.factory import (
    AssignmentRule,
    InitialAssignment,
    Model,
    Parameter,
    RateRule,
    create_model,
)
from sbmlutils.validation import (
    ConstructionDiagnostic,
    ConstructionError,
    check,
    collect_construction_diagnostics,
    record_construction_diagnostic,
)


@pytest.mark.parametrize("element", [AssignmentRule, RateRule, InitialAssignment])
def test_unknown_target_policy(tmp_path: Path, element: type) -> None:
    """Defaults retain auto-creation; strict mode protects existing output."""
    item = element("typo", "1")
    model = (
        Model("m", assignments=[item])
        if element is InitialAssignment
        else Model("m", rules=[item])
    )
    path = tmp_path / "model.xml"
    result = create_model(model, path, validate=False)
    assert libsbml.readSBMLFromFile(str(path)).getModel().getParameter("typo")
    assert result.diagnostics[0].code == "implicit_parameter"
    assert result.diagnostics[0].example == "typo"
    path.write_text("existing document", encoding="utf-8")
    with pytest.raises(ConstructionError) as caught:
        create_model(model, path, strict=True, validate=False, create_antimony=True)
    assert caught.value.diagnostics[0].severity == "error"
    assert path.read_text(encoding="utf-8") == "existing document"
    assert not path.with_suffix(".ant").exists()


def test_declared_target_strict(tmp_path: Path) -> None:
    """Explicit targets need no implicit parameter diagnostics."""
    model = Model(
        "m",
        parameters=[Parameter("p", 1, constant=False)],
        rules=[AssignmentRule("p", "2")],
    )
    result = create_model(model, tmp_path / "m.xml", strict=True, validate=False)
    assert result.diagnostics == ()
    assert result.validation is None


def test_unsupported_attribute_grouped(tmp_path: Path) -> None:
    """Repeated unsupported rule names are visible even when SBML is unchecked."""
    model = Model(
        "m",
        parameters=[Parameter(f"p{i}", 1, constant=False) for i in range(5)],
        rules=[AssignmentRule(f"p{i}", "1", name=f"r{i}") for i in range(5)],
    )
    result = create_model(model, tmp_path / "m.xml", validate=False)
    losses = [d for d in result.diagnostics if d.code == "unsupported_attribute"]
    assert len(losses) == 1
    assert losses[0].count == 5
    path = tmp_path / "strict.xml"
    with pytest.raises(ConstructionError):
        create_model(model, path, strict=True, validate=False)
    assert not path.exists()
    # The supported level/version writes names and does not report these losses.
    supported = create_model(
        model, tmp_path / "supported.xml", sbml_version=2, strict=True, validate=False
    )
    assert supported.diagnostics == ()


def test_failed_setter_recorded(tmp_path: Path) -> None:
    """An invalid requested ID produces a checked native-operation finding."""
    model = Model("m", parameters=[Parameter("bad id", 1)])
    result = create_model(model, tmp_path / "m.xml", validate=False)
    assert any(d.code == "libsbml_operation_failed" for d in result.diagnostics)
    with pytest.raises(ConstructionError):
        create_model(model, tmp_path / "strict.xml", validate=False, strict=True)


def test_nested_scope_cleanup_and_snapshots() -> None:
    """An inner scope cannot consume or mutate an outer diagnostic snapshot."""
    inner_findings: list[ConstructionDiagnostic] = []

    def fail_inside_scope() -> None:
        with collect_construction_diagnostics() as inner:
            check(None, "inner")
            inner_findings.extend(inner.diagnostics)
            raise RuntimeError("test")

    with collect_construction_diagnostics() as outer:
        check(libsbml.LIBSBML_INVALID_ATTRIBUTE_VALUE, "outer")
        snapshot = outer.diagnostics
        with pytest.raises(RuntimeError):
            fail_inside_scope()
        check(libsbml.LIBSBML_INVALID_ATTRIBUTE_VALUE, "outer again")
    assert snapshot[0].count == 1
    assert outer.diagnostics[0].count == 2
    assert inner_findings[0].example == "inner"
    check(None, "outside")
    assert len(outer.diagnostics) == 1


def test_concurrent_scopes() -> None:
    """Threads collect only their own findings without retaining native objects."""

    def collect(index: int) -> str | None:
        with collect_construction_diagnostics() as scope:
            for _ in range(100):
                record_construction_diagnostic("test", "cause", example=str(index))
            assert len(scope.diagnostics) == 1
            assert scope.diagnostics[0].count == 100
            return scope.diagnostics[0].example

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(collect, range(12))) == [str(i) for i in range(12)]


def test_unsupported_content(tmp_path: Path) -> None:
    """Content losses use the number of omitted pieces, not just elements."""
    from sbmlutils.factory import KeyValuePair, Package

    model = Model(
        "m",
        packages=[Package.FBC_V2],
        parameters=[
            Parameter(
                "p",
                1,
                keyValuePairs=[
                    KeyValuePair(key="one", value="1", uri=None),
                    KeyValuePair(key="two", value="2", uri=None),
                ],
            )
        ],
    )
    result = create_model(model, tmp_path / "m.xml", validate=False)
    loss = next(d for d in result.diagnostics if d.code == "unsupported_content")
    assert loss.count == 2
    with pytest.raises(ConstructionError):
        create_model(model, tmp_path / "strict.xml", strict=True, validate=False)


def test_retained_annotation_is_informational(tmp_path: Path) -> None:
    """Strict construction accepts resources which are preserved verbatim."""
    from sbmlutils.factory import Compartment, Species
    from sbmlutils.metadata import BQB

    resource = "urn:miriam::bar"
    model = Model(
        "m",
        compartments=[Compartment("c", 1)],
        species=[Species("s", "c", initialAmount=1, annotations=[(BQB.IS, resource)])],
    )
    result = create_model(model, tmp_path / "m.xml", strict=True, validate=False)
    finding = next(
        d for d in result.diagnostics if d.code == "annotation_resource_fallback"
    )
    assert finding.severity == "info"
    doc = libsbml.readSBMLFromFile(str(result.sbml_path))
    assert doc.getModel().getSpecies("s").getCVTerm(0).getResourceURI(0) == resource
