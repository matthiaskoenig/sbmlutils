"""Test SBML validation."""

import gc
import logging
from pathlib import Path

import libsbml
import pytest

from sbmlutils.io.sbml import (
    ValidationOptions,
    ValidationResult,
    read_sbml,
    validate_sbml,
)
from sbmlutils.resources import (
    BASIC_SBML,
    DEMO_SBML,
    GALACTOSE_SINGLECELL_SBML,
    VDP_SBML,
)
from sbmlutils.validation import ScopedLossCollector, file_uri, validate_doc


@pytest.mark.parametrize(
    "sbml_path, ucheck, n_all",
    [
        (DEMO_SBML, True, 0),
        (GALACTOSE_SINGLECELL_SBML, True, 0),
        (BASIC_SBML, True, 0),
        (VDP_SBML, False, 0),
    ],
)
def test_sbml_validation(sbml_path: Path, ucheck: bool, n_all: int) -> None:
    """Test SBML validation."""
    v_results = validate_sbml(
        source=sbml_path, validation_options=ValidationOptions(units_consistency=ucheck)
    )
    assert v_results
    assert n_all == v_results.all_count


@pytest.mark.parametrize(
    "options",
    [
        ValidationOptions(),
        ValidationOptions(internal_consistency=False),
        ValidationOptions(log_errors=False),
        ValidationOptions(general_consistency=False),
        ValidationOptions(identifier_consistency=False),
        ValidationOptions(mathml_consistency=False),
        ValidationOptions(units_consistency=False),
        ValidationOptions(sbo_consistency=False),
        ValidationOptions(overdetermined_model=False),
        ValidationOptions(modeling_practice=False),
    ],
)
def test_sbml_validation_options(options: ValidationOptions) -> None:
    """Test options for SBML validation."""
    v_results: ValidationResult = validate_sbml(
        source=DEMO_SBML, validation_options=options
    )
    assert v_results


_SBML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
<model id="{model_id}"{attributes}/>
</sbml>"""


def _error_ids(result: ValidationResult) -> list[int]:
    """Get the ids of the errors of a result."""
    return [error.getErrorId() for error in result.errors]


def test_validation_reports_read_errors_once() -> None:
    """A read error is part of the result, exactly once."""
    sbml = _SBML_TEMPLATE.format(model_id="m", attributes=' foo="1"')
    # the result refers to the error log of the document, which has to stay alive
    doc = read_sbml(sbml, promote=False, validate=False)
    result = validate_doc(doc, ValidationOptions(log_errors=False))
    assert _error_ids(result) == [libsbml.AllowedAttributesOnModel]
    assert not result.is_valid()


def test_validation_reports_new_errors_of_each_check() -> None:
    """The errors of a check are the ones it added to the log, not the first ones."""
    sbml = _SBML_TEMPLATE.format(model_id="1m", attributes="")
    doc = read_sbml(sbml, promote=False, validate=False)
    assert doc.getNumErrors() == 1
    result = validate_doc(doc, ValidationOptions(log_errors=False))
    # the read error once, the internal consistency check adds its own
    assert result.error_count == 2
    assert result.warning_count == 0


def test_validation_of_valid_model_has_no_errors() -> None:
    """A valid model reports nothing."""
    result = validate_sbml(DEMO_SBML, ValidationOptions(log_errors=False))
    assert result.is_perfect()


@pytest.mark.parametrize(
    "path, uri",
    [
        ("/home/user/model.xml", "file:///home/user/model.xml"),
        ("C:\\models\\model.xml", "file:///C:/models/model.xml"),
        ("C:/models/model.xml", "file:///C:/models/model.xml"),
        ("https://example.org/model.xml", "https://example.org/model.xml"),
        ("file:///tmp/model.xml", "file:///tmp/model.xml"),
        ("<SBMLDocument object at 0x1>", "<SBMLDocument object at 0x1>"),
        ("model.xml", "model.xml"),
    ],
)
def test_file_uri(path: str, uri: str) -> None:
    """Paths, including windows paths, become file URIs, other titles stay."""
    assert file_uri(path) == uri


def test_scoped_loss_collector_reports_remaining_groups_on_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A group which fails to report does not lose the others."""
    reported: list[str] = []

    def report(key: str, value: int) -> None:
        if key == "b":
            raise ValueError("cannot report b")
        reported.append(key)

    collector: ScopedLossCollector[str, int] = ScopedLossCollector(
        "test_losses", report
    )
    with (
        caplog.at_level(logging.ERROR, logger="sbmlutils.validation"),
        collector.scope(),
    ):
        for key in ("a", "b", "c"):
            assert collector.group(key, lambda: 1) == 1
    assert reported == ["a", "c"]
    assert "b" in caplog.text


def test_scoped_loss_collector_does_not_mask_body_exception() -> None:
    """The exception of the body propagates even if reporting fails."""

    def report(key: str, value: int) -> None:
        raise ValueError("cannot report")

    collector: ScopedLossCollector[str, int] = ScopedLossCollector(
        "test_losses", report
    )
    with pytest.raises(KeyError), collector.scope():
        collector.group("a", lambda: 1)
        raise KeyError("body")


def test_validation_result_outlives_the_document() -> None:
    """The errors of a result are snapshots, not references into a freed log."""
    sbml = _SBML_TEMPLATE.format(model_id="m", attributes=' foo="1"')
    result = validate_sbml(sbml, ValidationOptions(log_errors=False))
    gc.collect()
    assert _error_ids(result) == [libsbml.AllowedAttributesOnModel]
    assert "foo" in result.errors[0].getMessage()
    assert result.errors[0].getSeverity() == libsbml.LIBSBML_SEV_ERROR


def test_read_errors_are_logged_once(caplog: pytest.LogCaptureFixture) -> None:
    """With `validate` the read errors are logged by the validation only."""
    sbml = _SBML_TEMPLATE.format(model_id="m", attributes=' foo="1"')
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        read_sbml(sbml, promote=False, validate=True)
    assert caplog.text.count("Invalid attribute found on the Model object") == 1
