"""Test parsing of SBML."""

import logging
from pathlib import Path

import libsbml
import pytest
from pymetadata.omex import ManifestEntry, Omex

from sbmlutils.factory import Model, UncertParameter, UncertSpan, create_model
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import sbml_paths_idfn
from sbmlutils.validation import ValidationOptions

#: the biomodels archives are test data of the repository, they are not part of
#: the distribution, see `[tool.hatch.build]` in `pyproject.toml`
BIOMODELS_DIR = (
    Path(__file__).parent.parent
    / "src"
    / "sbmlutils"
    / "resources"
    / "models"
    / "biomodels"
)

omex_paths: list[Path] = []
for k in range(100):
    path: Path = BIOMODELS_DIR / f"BIOMD0000000{k:0>3}.omex"
    if path.exists():
        omex_paths.append(path)


@pytest.mark.parametrize("omex_path", omex_paths, ids=sbml_paths_idfn)
def test_model_from_biomodels_omex(omex_path: Path, tmp_path: Path) -> None:
    """Test creation of json for paths."""
    assert omex_path.exists()

    omex = Omex().from_omex(omex_path)
    entry: ManifestEntry
    for entry in omex.manifest.entries:
        if entry.is_sbml():
            sbml_path: Path = omex.get_path(entry.location)

            print(str(sbml_path))
            m: Model = sbml_to_model(sbml_path)
            print(m)
            create_model(
                model=m,
                filepath=tmp_path / "models.xml",
                sbml_level=3,
                sbml_version=2,
                validation_options=ValidationOptions(units_consistency=False),
            )


#: an fbc v2 model whose objective omits the required `fbc:type`
_OBJECTIVE_WITHOUT_TYPE: str = """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core"
      xmlns:fbc="http://www.sbml.org/sbml/level3/version1/fbc/version2"
      level="3" version="2" fbc:required="false">
  <model id="no_objective_type" fbc:strict="false">
    <listOfCompartments>
      <compartment id="c" size="1" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species id="S1" compartment="c" initialAmount="1"
               hasOnlySubstanceUnits="false" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    <listOfReactions>
      <reaction id="R1" reversible="false">
        <listOfReactants>
          <speciesReference species="S1" stoichiometry="1" constant="true"/>
        </listOfReactants>
      </reaction>
    </listOfReactions>
    <fbc:listOfObjectives fbc:activeObjective="obj">
      <fbc:objective fbc:id="obj">
        <fbc:listOfFluxObjectives>
          <fbc:fluxObjective fbc:reaction="R1" fbc:coefficient="1"/>
        </fbc:listOfFluxObjectives>
      </fbc:objective>
    </fbc:listOfObjectives>
  </model>
</sbml>
"""


def test_objective_without_a_type_is_read_and_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that an objective without `fbc:type` is read, not raised on.

    `fbc:type` is required on an objective, so a document without it is
    invalid, and `Objective` has no field for a missing one:
    `Objective.normalize_objective_type` refuses both `None` and the empty
    string `libsbml.Objective.getType()` returns for it. A parser reads what
    is there and reports the problem, it does not turn an invalid document
    into an exception, so the objective is read with the `maximize` of the
    `Objective` default and the problem is logged.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.parser"):
        m: Model = sbml_to_model(_OBJECTIVE_WITHOUT_TYPE)

    (objective,) = m.objectives
    assert objective.sid == "obj"
    assert objective.objectiveType == libsbml.OBJECTIVE_TYPE_MAXIMIZE
    assert objective.active is True
    assert [
        record.getMessage()
        for record in caplog.records
        if record.name == "sbmlutils.parser" and "fbc:type" in record.getMessage()
    ] != []


#: an uncertainty on a unit definition, which libsbml reads and `UnitDefinition`
#: has no field for
_UNCERTAINTY_ON_A_UNIT_DEFINITION = """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core"
      xmlns:distrib="http://www.sbml.org/sbml/level3/version1/distrib/version1"
      level="3" version="2" distrib:required="true">
  <model id="uncertainty_on_a_unit_definition">
    <listOfUnitDefinitions>
      <unitDefinition id="mM">
        <distrib:listOfUncertainties>
          <distrib:uncertainty>
            <distrib:uncertParameter distrib:value="0.1" distrib:type="standardDeviation"/>
          </distrib:uncertainty>
        </distrib:listOfUncertainties>
        <listOfUnits>
          <unit kind="mole" exponent="1" scale="-3" multiplier="1"/>
        </listOfUnits>
      </unitDefinition>
    </listOfUnitDefinitions>
    <listOfParameters>
      <parameter id="p1" value="1" units="mM" constant="true">
        <distrib:listOfUncertainties>
          <distrib:uncertainty distrib:name="p1 is 1 +- 0.1">
            <distrib:uncertSpan distrib:type="range" distrib:valueLower="0.9"
                                distrib:valueUpper="1.1"/>
            <distrib:uncertParameter distrib:value="1" distrib:units="mM"
                                     distrib:type="mean"/>
          </distrib:uncertainty>
        </distrib:listOfUncertainties>
      </parameter>
    </listOfParameters>
  </model>
</sbml>
"""


def test_uncertainty_of_a_parameter_is_read() -> None:
    """Test that the uncertainty of an element is read with its children in order.

    The children of an uncertainty are one list in SBML, in which a span and a
    parameter can appear in any order, and `Uncertainty.uncertParameters` is
    that list.
    """
    m: Model = sbml_to_model(_UNCERTAINTY_ON_A_UNIT_DEFINITION)

    (parameter,) = m.parameters
    assert parameter.uncertainties is not None
    (uncertainty,) = parameter.uncertainties
    assert uncertainty.name == "p1 is 1 +- 0.1"
    span, mean = uncertainty.uncertParameters
    assert isinstance(span, UncertSpan)
    assert (span.type, span.valueLower, span.valueUpper) == (
        libsbml.DISTRIB_UNCERTTYPE_RANGE,
        0.9,
        1.1,
    )
    assert isinstance(mean, UncertParameter)
    assert (mean.type, mean.value, mean.unit) == (
        libsbml.DISTRIB_UNCERTTYPE_MEAN,
        1.0,
        "mM",
    )


def test_uncertainty_of_an_element_which_cannot_carry_one_is_reported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that an uncertainty which cannot be held is reported, not dropped in silence.

    libsbml reads an uncertainty from every element, `UnitDefinition` of
    sbmlutils has no field for one, and a value which is read and then dropped
    by the writer is a loss nobody sees. The rest of the document is read as
    usual, see `_drop_uncertainties`.
    """
    with caplog.at_level(logging.ERROR, logger="sbmlutils.parser"):
        m: Model = sbml_to_model(_UNCERTAINTY_ON_A_UNIT_DEFINITION)

    (udef,) = m.units
    assert udef.sid == "mM"
    errors = [
        record.getMessage()
        for record in caplog.records
        if record.name == "sbmlutils.parser" and "are lost" in record.getMessage()
    ]
    assert len(errors) == 1, caplog.records
    assert "unitDefinition" in errors[0] and "mM" in errors[0]
