"""Tests of the structural comparison which the package round trip is judged by.

A round trip of the fbc, distrib and comp packages is checked by `structural_diff` of `tests/structural.py`, since simulation and validation are both blind to these packages, see its docstring for the comparison policy. A comparison which reports nothing on a damaged document is blind as well, so these tests prove it sees each kind of loss: they damage one construct in a copy of a real fixture and assert that exactly that construct is reported, and they assert that an undamaged document is reported as unchanged.

They never assert what `sbml_to_model` loses today. Those losses are removed one by one by the tasks which follow, and a test pinned to them would break with every fix. The losses of the current parser are measured by `scripts/package_report.py` instead. A loss which is not going to be removed is pinned by a test of its own, which spells out exactly how much is lost and fails as soon as one element more goes missing: the `sboTerm` of the `and` and `or` nodes of a gene product association, which `Reaction.geneProductAssociation` has no place for, see `test_roundtrip_loses_only_the_sboterm_of_an_association_node`.

The cases of the SBML test suite are resolved from the checkout, see `tests/test_roundtrip.py`, since the installed package does not contain them.
"""

import logging
import re
import shutil
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import libsbml
import pytest
from pymetadata.core.annotation import RDFAnnotation
from pymetadata.core.miriam import BQB
from structural import (
    ABSENT,
    DISTRIB_CSYMBOL,
    ELEMENT,
    PACKAGES,
    WHITELIST,
    Attributes,
    Difference,
    Normalization,
    Snapshot,
    comparable_document,
    diff_snapshots,
    roundtrip_document,
    snapshot,
    snapshots,
    structural_diff,
)
from test_roundtrip import SEMANTIC_DIR, requires_testsuite, testsuite_case

from sbmlutils import RESOURCES_DIR
from sbmlutils.factory import (
    Compartment,
    EquationPart,
    KeyValuePair,
    Model,
    Objective,
    Package,
    Parameter,
    Reaction,
    ReactionEquation,
    Species,
    UserDefinedConstraint,
    UserDefinedConstraintComponent,
    create_model,
)
from sbmlutils.parser import sbml_to_model
from sbmlutils.resources import (
    COMP_ICG_BODY,
    COMP_ICG_BODY_FLAT,
    DISTRIB_COMP_FLAT_SBML,
    DISTRIB_COMP_SBML,
    DISTRIB_DISTRIBUTIONS_SBML,
    DISTRIB_UNCERTAINTIES_SBML,
    EXAMPLES_DIR,
    FBC_ECOLI_CORE_SBML,
    FBC_RECON3D_SBML,
)
from sbmlutils.validation import ValidationOptions, validate_doc

#: the uncertainties of distrib, with parameters, spans and math
UNCERTAINTY_SBML: Path = RESOURCES_DIR / "distrib" / "uncertainty.xml"
#: the distributions of distrib, as csymbols in the math of initial assignments
DISTRIB_ALL_SBML: Path = RESOURCES_DIR / "distrib" / "distrib_all.xml"
#: gene product associations whose `and` and `or` nodes carry an sboTerm
ECOLI_CORE_DISTRIB_SBML: Path = RESOURCES_DIR / "distrib" / "e_coli_core.xml"
#: gene product associations whose `and` and `or` nodes carry an sboTerm, and an
#: uncertainty
ECOLI_EXPRESSION_SBML: Path = RESOURCES_DIR / "distrib" / "e_coli_core_expression.xml"
#: the only user-defined constraints of the repository
FBC_UDC_SBML: Path = EXAMPLES_DIR / "fbc_user_defined_constraints.xml"
#: the key-value pairs of fbc version 3, on a parameter
FBC_KVP_SBML: Path = EXAMPLES_DIR / "fbc" / "fbc_key_value_pair.xml"
#: one distribution of distrib, as a csymbol in the math of an assignment rule
DISTRIB_NORMAL_SBML: Path = RESOURCES_DIR / "distrib" / "distrib_normal.xml"
#: an uncertainty on a compartment, beside fbc and comp content
MODEL_SBML: Path = EXAMPLES_DIR / "model.xml"


#: the source of a fixture: an SBML file, or a model definition built on demand
Source = Path | Callable[[], Model]


def _source_path(source: Source, tmp_path: Path) -> Path:
    """Resolve the source of a fixture to an SBML file.

    Args:
        source: an SBML file, or a function returning a model definition which is built and created first
        tmp_path: directory a model definition is created in

    Returns:
        the path of the SBML file
    """
    if isinstance(source, Path):
        return source
    model = source()
    sbml_path = tmp_path / f"{model.sid}.xml"
    create_model(model=model, filepath=sbml_path, validate=False)
    return sbml_path


def _read(sbml_path: Path) -> libsbml.SBMLDocument:
    """Read an SBML file with libsbml.

    Args:
        sbml_path: path of the SBML file

    Returns:
        the document, which the caller has to hold for as long as it uses any object of it
    """
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    assert doc.getModel() is not None, f"no model in '{sbml_path}'"
    return doc


# ---------------------------------------------------------------------------
# the damages, each applied to a document read from its fixture
# ---------------------------------------------------------------------------
def _fbc(doc: libsbml.SBMLDocument) -> libsbml.FbcModelPlugin:
    """Get the fbc plugin of the model of a document, which the caller holds."""
    plugin: libsbml.FbcModelPlugin = doc.getModel().getPlugin("fbc")
    return plugin


def _comp(doc: libsbml.SBMLDocument) -> libsbml.CompModelPlugin:
    """Get the comp plugin of the model of a document, which the caller holds."""
    plugin: libsbml.CompModelPlugin = doc.getModel().getPlugin("comp")
    return plugin


def _first(doc: libsbml.SBMLDocument, accept: Callable[[Any], bool]) -> Any:
    """Find the first element of a document which is accepted.

    Args:
        doc: the document, which the caller holds
        accept: whether an element is the one looked for

    Returns:
        the first accepted element of the document, in document order
    """
    for element in doc.getListOfAllElements():
        if accept(element):
            return element
    raise AssertionError("the fixture has no such element")


def _drop_gene_product(doc: libsbml.SBMLDocument) -> None:
    """Remove a gene product."""
    assert _fbc(doc).removeGeneProduct("G_b1241") is not None


def _change_gene_product_label(doc: libsbml.SBMLDocument) -> None:
    """Change the label of a gene product."""
    gene_product: libsbml.GeneProduct = _fbc(doc).getGeneProduct("G_b1241")
    assert gene_product.setLabel("b9999") == libsbml.LIBSBML_OPERATION_SUCCESS


def _drop_gene_product_annotation(doc: libsbml.SBMLDocument) -> None:
    """Remove the RDF annotation of a gene product."""
    gene_product: libsbml.GeneProduct = _fbc(doc).getGeneProduct("G_b1241")
    assert gene_product.unsetCVTerms() == libsbml.LIBSBML_OPERATION_SUCCESS


def _change_flux_bound(doc: libsbml.SBMLDocument) -> None:
    """Point the upper flux bound of a reaction at another parameter."""
    reaction: libsbml.Reaction = doc.getModel().getReaction("R_PFK")
    plugin: libsbml.FbcReactionPlugin = reaction.getPlugin("fbc")
    assert (
        plugin.setUpperFluxBound("cobra_0_bound") == libsbml.LIBSBML_OPERATION_SUCCESS
    )


def _change_v1_flux_bound_value(doc: libsbml.SBMLDocument) -> None:
    """Change the value of an fbc v1 flux bound."""
    flux_bound: libsbml.FluxBound = _fbc(doc).getFluxBound(0)
    assert flux_bound.setValue(42.0) == libsbml.LIBSBML_OPERATION_SUCCESS


def _drop_objective(doc: libsbml.SBMLDocument) -> None:
    """Remove the objective, and with it its flux objectives."""
    assert _fbc(doc).removeObjective("obj") is not None


def _change_flux_objective(doc: libsbml.SBMLDocument) -> None:
    """Change the coefficient of a flux objective."""
    flux_objective: libsbml.FluxObjective = (
        _fbc(doc).getObjective(0).getFluxObjective(0)
    )
    assert flux_objective.setCoefficient(2.0) == libsbml.LIBSBML_OPERATION_SUCCESS


def _unset_active_objective(doc: libsbml.SBMLDocument) -> None:
    """Make no objective the active one."""
    assert _fbc(doc).unsetActiveObjectiveId() == libsbml.LIBSBML_OPERATION_SUCCESS


def _flip_strict(doc: libsbml.SBMLDocument) -> None:
    """Flip `fbc:strict` of a strict model."""
    assert _fbc(doc).getStrict()
    assert _fbc(doc).setStrict(False) == libsbml.LIBSBML_OPERATION_SUCCESS


def _change_gene_product_association(doc: libsbml.SBMLDocument) -> None:
    """Turn the `or` of an association into an `and`."""
    reaction: libsbml.Reaction = doc.getModel().getReaction("R_PFK")
    plugin: libsbml.FbcReactionPlugin = reaction.getPlugin("fbc")
    gpa: libsbml.GeneProductAssociation = plugin.getGeneProductAssociation()
    assert gpa.getAssociation().toInfix(True) == "(G_b3916 or G_b1723)"
    assert gpa.setAssociation("G_b3916 and G_b1723", True, False) == (
        libsbml.LIBSBML_OPERATION_SUCCESS
    )


def _change_charge(doc: libsbml.SBMLDocument) -> None:
    """Change the charge of a species."""
    species: libsbml.Species = doc.getModel().getSpecies("M_glc__D_e")
    plugin: libsbml.FbcSpeciesPlugin = species.getPlugin("fbc")
    assert plugin.setCharge(1) == libsbml.LIBSBML_OPERATION_SUCCESS


def _drop_chemical_formula(doc: libsbml.SBMLDocument) -> None:
    """Remove the chemical formula of a species."""
    species: libsbml.Species = doc.getModel().getSpecies("M_glc__D_e")
    plugin: libsbml.FbcSpeciesPlugin = species.getPlugin("fbc")
    assert plugin.unsetChemicalFormula() == libsbml.LIBSBML_OPERATION_SUCCESS


def _change_constraint_component(doc: libsbml.SBMLDocument) -> None:
    """Change the coefficient of a user-defined constraint component."""
    constraint: libsbml.UserDefinedConstraint = _fbc(doc).getUserDefinedConstraint(0)
    component: libsbml.UserDefinedConstraintComponent = (
        constraint.getUserDefinedConstraintComponent(0)
    )
    # fbc v3 references a parameter as the coefficient
    assert component.getCoefficient() == "coef_plus_one"
    assert component.setCoefficient("Avar") == libsbml.LIBSBML_OPERATION_SUCCESS


def _drop_user_defined_constraint(doc: libsbml.SBMLDocument) -> None:
    """Remove a user-defined constraint, and with it its components."""
    assert _fbc(doc).removeUserDefinedConstraint(1) is not None


def _change_key_value_pair(doc: libsbml.SBMLDocument) -> None:
    """Change the value of a key-value pair."""
    parameter: libsbml.Parameter = doc.getModel().getParameter("p1")
    plugin: libsbml.FbcSBasePlugin = parameter.getPlugin("fbc")
    kvp: libsbml.KeyValuePair = plugin.getKeyValuePair(0)
    assert kvp.setValue("48") == libsbml.LIBSBML_OPERATION_SUCCESS


def _drop_port(doc: libsbml.SBMLDocument) -> None:
    """Remove a port."""
    assert _comp(doc).removePort(0) is not None


def _drop_submodel(doc: libsbml.SBMLDocument) -> None:
    """Remove the submodel."""
    assert _comp(doc).removeSubmodel(0) is not None


def _drop_replaced_element(doc: libsbml.SBMLDocument) -> None:
    """Remove the replaced element of a compartment."""
    compartment: libsbml.Compartment = doc.getModel().getCompartment("Vbi")
    plugin: libsbml.CompSBasePlugin = compartment.getPlugin("comp")
    assert plugin.removeReplacedElement(0) is not None


def _change_external_model_definition(doc: libsbml.SBMLDocument) -> None:
    """Point the external model definition at another file."""
    plugin: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    definition: libsbml.ExternalModelDefinition = plugin.getExternalModelDefinition(0)
    assert definition.setSource("other.xml") == libsbml.LIBSBML_OPERATION_SUCCESS


def _truncate_sbaseref_chain(doc: libsbml.SBMLDocument) -> None:
    """Remove the innermost level of a nested `sBaseRef` chain."""
    sbaseref: libsbml.SBaseRef = _first(
        doc,
        lambda e: e.getElementName() == "sBaseRef" and e.isSetSBaseRef(),
    )
    assert sbaseref.unsetSBaseRef() == libsbml.LIBSBML_OPERATION_SUCCESS


def _change_model_definition_content(doc: libsbml.SBMLDocument) -> None:
    """Change the size of a compartment of a model definition."""
    plugin: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    definition: libsbml.ModelDefinition = plugin.getModelDefinition("moddef1")
    compartment: libsbml.Compartment = definition.getCompartment("C")
    assert compartment.setSize(42.0) == libsbml.LIBSBML_OPERATION_SUCCESS


def _drop_deletion(doc: libsbml.SBMLDocument) -> None:
    """Remove the deletion of a submodel."""
    submodel: libsbml.Submodel = _first(
        doc, lambda e: e.getElementName() == "submodel" and e.getNumDeletions() > 0
    )
    assert submodel.removeDeletion(0) is not None


def _drop_replaced_by(doc: libsbml.SBMLDocument) -> None:
    """Remove the replaced by of a parameter."""
    parameter: libsbml.Parameter = doc.getModel().getParameter(0)
    plugin: libsbml.CompSBasePlugin = parameter.getPlugin("comp")
    assert plugin.isSetReplacedBy()
    assert plugin.unsetReplacedBy() == libsbml.LIBSBML_OPERATION_SUCCESS


def _change_submodel_conversion_factor(doc: libsbml.SBMLDocument) -> None:
    """Change the extent conversion factor of a submodel."""
    submodel: libsbml.Submodel = _comp(doc).getSubmodel("sub1")
    assert submodel.getExtentConversionFactor() == "extentconv"
    assert submodel.setExtentConversionFactor("other") == (
        libsbml.LIBSBML_OPERATION_SUCCESS
    )


def _uncertainties(doc: libsbml.SBMLDocument) -> libsbml.ListOfUncertainties:
    """Get the uncertainties of the parameter `p1`, the document is held."""
    parameter: libsbml.Parameter = doc.getModel().getParameter("p1")
    plugin: libsbml.DistribSBasePlugin = parameter.getPlugin("distrib")
    uncertainties: libsbml.ListOfUncertainties = plugin.getListOfUncertainties()
    return uncertainties


def _reorder_uncertainty_children(doc: libsbml.SBMLDocument) -> None:
    """Move the first uncertParameter of an uncertainty behind its span."""
    uncertainty: libsbml.Uncertainty = _uncertainties(doc).get(0)
    children: libsbml.ListOfUncertParameters = uncertainty.getListOfUncertParameters()
    assert [child.getElementName() for child in children] == [
        "uncertParameter",
        "uncertParameter",
        "uncertSpan",
    ]
    first: libsbml.UncertParameter = children.remove(0)
    assert children.appendAndOwn(first) == libsbml.LIBSBML_OPERATION_SUCCESS


def _drop_uncertainty(doc: libsbml.SBMLDocument) -> None:
    """Remove an uncertainty, and with it its parameters."""
    assert _uncertainties(doc).remove(1) is not None


def _change_uncertainty_math(doc: libsbml.SBMLDocument) -> None:
    """Change the math of the distribution of an uncertainty."""
    uncertainty: libsbml.Uncertainty = _uncertainties(doc).get(3)
    parameter: libsbml.UncertParameter = uncertainty.getUncertParameter(0)
    math: libsbml.ASTNode = libsbml.parseL3Formula("5 * p1")
    assert parameter.setMath(math) == libsbml.LIBSBML_OPERATION_SUCCESS


def _change_uncert_span(doc: libsbml.SBMLDocument) -> None:
    """Change the upper value of an uncertSpan."""
    uncertainty: libsbml.Uncertainty = _uncertainties(doc).get(0)
    span: libsbml.UncertSpan = uncertainty.getUncertParameter(2)
    assert span.setValueUpper(9.0) == libsbml.LIBSBML_OPERATION_SUCCESS


def _drop_distribution(doc: libsbml.SBMLDocument) -> None:
    """Replace the draw from a normal distribution by a number."""
    assignment: libsbml.InitialAssignment = doc.getModel().getInitialAssignment(
        "p_normal_1"
    )
    math: libsbml.ASTNode = libsbml.parseL3Formula("0")
    assert assignment.setMath(math) == libsbml.LIBSBML_OPERATION_SUCCESS


@dataclass(frozen=True)
class Mutation:
    """A damage to one construct of a fixture.

    Attributes:
        source: the fixture, an SBML file or a function returning a model definition
        damage: damages a document read from the source, in place
        constructs: the constructs which the damage changes, and nothing else
    """

    source: Source
    damage: Callable[[libsbml.SBMLDocument], None]
    constructs: frozenset[str]


def _mutation(
    source: Source,
    damage: Callable[[libsbml.SBMLDocument], None],
    *constructs: str,
) -> Mutation:
    """Create a mutation."""
    return Mutation(source, damage, frozenset(constructs))


#: every kind of loss the comparison must see, by name
MUTATIONS: dict[str, Mutation] = {
    # fbc
    "drop_gene_product": _mutation(
        FBC_ECOLI_CORE_SBML, _drop_gene_product, "fbc.geneProduct"
    ),
    "change_gene_product_label": _mutation(
        FBC_ECOLI_CORE_SBML, _change_gene_product_label, "fbc.geneProduct"
    ),
    "drop_gene_product_annotation": _mutation(
        FBC_ECOLI_CORE_SBML, _drop_gene_product_annotation, "fbc.geneProduct"
    ),
    "change_flux_bound": _mutation(
        FBC_ECOLI_CORE_SBML, _change_flux_bound, "fbc.fluxBound"
    ),
    "change_v1_flux_bound_value": _mutation(
        testsuite_case("01186"), _change_v1_flux_bound_value, "fbc.fluxBound"
    ),
    "drop_objective": _mutation(
        FBC_ECOLI_CORE_SBML, _drop_objective, "fbc.objective", "fbc.fluxObjective"
    ),
    "change_flux_objective": _mutation(
        FBC_ECOLI_CORE_SBML, _change_flux_objective, "fbc.fluxObjective"
    ),
    "unset_active_objective": _mutation(
        FBC_ECOLI_CORE_SBML, _unset_active_objective, "fbc.objective"
    ),
    "flip_strict": _mutation(FBC_ECOLI_CORE_SBML, _flip_strict, "fbc.strict"),
    "change_gene_product_association": _mutation(
        FBC_ECOLI_CORE_SBML,
        _change_gene_product_association,
        "fbc.geneProductAssociation",
    ),
    "change_charge": _mutation(FBC_ECOLI_CORE_SBML, _change_charge, "fbc.charge"),
    "drop_chemical_formula": _mutation(
        FBC_ECOLI_CORE_SBML, _drop_chemical_formula, "fbc.chemicalFormula"
    ),
    "change_constraint_component": _mutation(
        FBC_UDC_SBML,
        _change_constraint_component,
        "fbc.userDefinedConstraintComponent",
    ),
    "drop_user_defined_constraint": _mutation(
        FBC_UDC_SBML,
        _drop_user_defined_constraint,
        "fbc.userDefinedConstraint",
        "fbc.userDefinedConstraintComponent",
    ),
    "change_key_value_pair": _mutation(
        FBC_KVP_SBML, _change_key_value_pair, "fbc.keyValuePair"
    ),
    # comp
    "drop_port": _mutation(COMP_ICG_BODY, _drop_port, "comp.port"),
    "drop_submodel": _mutation(COMP_ICG_BODY, _drop_submodel, "comp.submodel"),
    "drop_replaced_element": _mutation(
        COMP_ICG_BODY, _drop_replaced_element, "comp.replacedElement"
    ),
    "change_external_model_definition": _mutation(
        COMP_ICG_BODY,
        _change_external_model_definition,
        "comp.externalModelDefinition",
    ),
    "truncate_sbaseref_chain": _mutation(
        testsuite_case("01132"), _truncate_sbaseref_chain, "comp.sBaseRef"
    ),
    "change_model_definition_content": _mutation(
        testsuite_case("01132"),
        _change_model_definition_content,
        "comp.modelDefinition.compartment",
    ),
    "drop_deletion": _mutation(
        testsuite_case("01157"), _drop_deletion, "comp.deletion"
    ),
    "drop_replaced_by": _mutation(
        testsuite_case("01128"), _drop_replaced_by, "comp.replacedBy"
    ),
    "change_submodel_conversion_factor": _mutation(
        testsuite_case("01143"), _change_submodel_conversion_factor, "comp.submodel"
    ),
    # distrib
    "reorder_uncertainty_children": _mutation(
        UNCERTAINTY_SBML, _reorder_uncertainty_children, "distrib.uncertParameter"
    ),
    "drop_uncertainty": _mutation(
        UNCERTAINTY_SBML,
        _drop_uncertainty,
        "distrib.uncertainty",
        "distrib.uncertParameter",
    ),
    "change_uncertainty_math": _mutation(
        UNCERTAINTY_SBML, _change_uncertainty_math, "distrib.uncertParameter"
    ),
    "change_uncert_span": _mutation(
        UNCERTAINTY_SBML, _change_uncert_span, "distrib.uncertParameter"
    ),
    "drop_distribution": _mutation(
        DISTRIB_ALL_SBML, _drop_distribution, "distrib.csymbol"
    ),
}


def _damaged_copy(
    mutation: str, tmp_path: Path
) -> tuple[libsbml.SBMLDocument, libsbml.SBMLDocument]:
    """Read a fixture twice and damage the second copy.

    Args:
        mutation: the name of the mutation, see `MUTATIONS`
        tmp_path: directory a fixture defined by a model is created in

    Returns:
        the undamaged and the damaged document; the caller has to hold both for as long as it uses any object of them
    """
    sbml_path = _source_path(MUTATIONS[mutation].source, tmp_path)
    doc_in = _read(sbml_path)
    doc_damaged = _read(sbml_path)
    MUTATIONS[mutation].damage(doc_damaged)
    return doc_in, doc_damaged


def _param(value: Any, source: Source) -> Any:
    """Mark a parametrization whose fixture is a case of the vendored SBML test suite.

    The test suite is resolved from the checkout and is in neither the wheel nor an sdist, see the module docstring, so a parametrization which reads one of its cases has to skip where it is absent instead of failing on a file which is not there.

    Args:
        value: the value of the parametrization
        source: the fixture the parametrization reads

    Returns:
        the value, as a `pytest.param` marked `requires_testsuite` if the fixture is a test suite case
    """
    if isinstance(source, Path) and SEMANTIC_DIR in source.parents:
        return pytest.param(value, marks=[requires_testsuite])
    return value


@pytest.mark.parametrize(
    "mutation",
    [_param(name, mutation.source) for name, mutation in MUTATIONS.items()],
)
def test_structural_diff_sees_each_kind_of_loss(mutation: str, tmp_path: Path) -> None:
    """A comparison which reports nothing on a damaged document is blind.

    Each mutation removes or alters exactly one construct in a copy of a real fixture; the comparison must report that construct and only that.
    """
    doc_in, doc_damaged = _damaged_copy(mutation, tmp_path)
    diffs = structural_diff(doc_in, doc_damaged)
    assert diffs, f"structural_diff missed a {mutation}"
    assert {d.construct for d in diffs} == MUTATIONS[mutation].constructs, diffs


#: fixtures which exercise every construct between them; the SBML test suite
#: cases are resolved from the checkout
FIXTURES: list[Path] = [
    FBC_ECOLI_CORE_SBML,
    ECOLI_EXPRESSION_SBML,
    FBC_UDC_SBML,
    COMP_ICG_BODY,
    UNCERTAINTY_SBML,
    DISTRIB_ALL_SBML,
    # fbc v1, two objectives
    testsuite_case("01191"),
    # fbc v2
    testsuite_case("01606"),
    # nested sBaseRef, replacedBy, ports
    testsuite_case("01132"),
    testsuite_case("01134"),
    # deletion by metaIdRef
    testsuite_case("01157"),
    # conversion factors of a submodel and of a replaced element
    testsuite_case("01143"),
    testsuite_case("01137"),
    # external model definition
    testsuite_case("01167"),
]

#: the fixtures as parametrizations, with the test suite cases marked to skip
#: where the vendored suite is absent
FIXTURE_PARAMS: list[Any] = [_param(path, path) for path in FIXTURES]


def fixture_idfn(sbml_path: Path) -> str:
    """Name a test by its fixture."""
    return sbml_path.name


@pytest.mark.parametrize("sbml_path", FIXTURE_PARAMS, ids=fixture_idfn)
def test_structural_diff_reports_nothing_on_an_undamaged_document(
    sbml_path: Path,
) -> None:
    """Test that the comparison reports no noise.

    A document is compared with itself and with its copy written and read back by libsbml. Neither changes any content, so any difference would be noise of the comparison.
    """
    doc = _read(sbml_path)
    doc_copy: libsbml.SBMLDocument = libsbml.readSBMLFromString(
        libsbml.writeSBMLToString(doc)
    )

    assert structural_diff(doc, doc) == []
    assert structural_diff(doc, doc_copy) == []


def test_structural_diff_reports_the_lost_element(tmp_path: Path) -> None:
    """Test that an element lost on one side is one difference, with its attributes."""
    doc_in, doc_damaged = _damaged_copy("drop_port", tmp_path)
    port: libsbml.Port = _comp(doc_in).getPort(0)

    (difference,) = structural_diff(doc_in, doc_damaged)

    assert difference.construct == "comp.port"
    assert difference.element_id == f"model/port:{port.getIdAttribute()}"
    assert difference.attribute == ELEMENT
    assert isinstance(difference.before, tuple)
    assert dict(difference.before)["idRef"] == port.getIdRef()
    assert difference.after == ABSENT


# ---------------------------------------------------------------------------
# completeness: the comparison sees every element and attribute libsbml reads
# ---------------------------------------------------------------------------
#: the nodes of an association, compared as its infix string
_ASSOCIATION_NODES: frozenset[str] = frozenset({"and", "or", "geneProductRef"})


def _construct_of(element: libsbml.SBase) -> str | None:
    """Name the construct an element of a document is compared as.

    This is an independent recount of what `snapshot` has to see: every element of a package, and every core element of a model definition.

    Args:
        element: an element of a document

    Returns:
        the construct, `None` for an element which is not compared on its own
    """
    name: str = element.getElementName()
    if name.startswith("listOf") or name in _ASSOCIATION_NODES:
        return None
    package: str = element.getPackageName()
    if package in ("fbc", "distrib", "comp"):
        return (
            "distrib.uncertParameter" if name == "uncertSpan" else f"{package}.{name}"
        )
    in_definition = element.getAncestorOfType(libsbml.SBML_COMP_MODELDEFINITION, "comp")
    if package == "core" and in_definition is not None:
        return f"comp.modelDefinition.{name}"
    return None


def _attributes_constructs(element: libsbml.SBase) -> list[str]:
    """Name the constructs which are attributes of a core element.

    Args:
        element: an element of a document

    Returns:
        the constructs the element carries
    """
    constructs: list[str] = []
    fbc = element.getPlugin("fbc")
    name: str = element.getElementName()
    if name == "species" and fbc is not None:
        if fbc.isSetCharge():
            constructs.append("fbc.charge")
        if fbc.isSetChemicalFormula():
            constructs.append("fbc.chemicalFormula")
    if (
        name == "reaction"
        and fbc is not None
        and (fbc.isSetLowerFluxBound() or fbc.isSetUpperFluxBound())
    ):
        constructs.append("fbc.fluxBound")
    if name in ("model", "modelDefinition") and fbc is not None and fbc.isSetStrict():
        constructs.append("fbc.strict")
    get_math = getattr(element, "getMath", None)
    math: libsbml.ASTNode | None = get_math() if get_math is not None else None
    if (
        element.getPackageName() == "core"
        and math is not None
        and DISTRIB_CSYMBOL in libsbml.writeMathMLToString(math)
    ):
        constructs.append("distrib.csymbol")
    return constructs


def _expected_constructs(doc: libsbml.SBMLDocument) -> Counter[str]:
    """Count the constructs a document has, independently of `snapshot`.

    Args:
        doc: a document at L3V2 and fbc version 2 or higher, which is held

    Returns:
        the number of elements of every construct
    """
    counts: Counter[str] = Counter()
    for package in ("fbc", "distrib", "comp"):
        if doc.getPlugin(package) is not None:
            counts[f"{package}.package"] += 1
    # the elements of a document include its model
    for element in doc.getListOfAllElements():
        construct = _construct_of(element)
        if construct is not None:
            counts[construct] += 1
        counts.update(_attributes_constructs(element))
    return counts


@pytest.mark.parametrize("sbml_path", FIXTURE_PARAMS, ids=fixture_idfn)
def test_snapshot_sees_every_element(sbml_path: Path) -> None:
    """Test that the comparison sees every package element libsbml reads.

    The snapshot is recounted from `getListOfAllElements`, which walks the whole document, so an element kind or a list the comparison forgot to walk is found here.
    """
    doc = comparable_document(_read(sbml_path))

    seen = Counter(construct for construct, _ in snapshot(doc))

    assert seen == _expected_constructs(doc)


#: the start tag of an element and its attributes, as libsbml writes them, and
#: the name and the value of one attribute
_START_TAG = re.compile(r"<[^\s>/]+((?:\s+[^\s=]+=\"[^\"]*\")*)\s*/?>")
_ATTRIBUTE = re.compile(r"([^\s=]+)=\"([^\"]*)\"")


def _written_attributes(element: libsbml.SBase) -> set[tuple[str, str]]:
    """Get the attributes libsbml writes on an element.

    Args:
        element: an element of a document, which is held

    Returns:
        the prefix and the local name of every attribute of its start tag, namespace declarations excluded, `metaid` spelled `metaId`; the prefix of an attribute without one is empty
    """
    match = _START_TAG.match(element.toSBML())
    assert match is not None, element.toSBML()[:200]
    written: set[tuple[str, str]] = set()
    for name, _value in _ATTRIBUTE.findall(match.group(1)):
        prefix, _, local = name.rpartition(":")
        if prefix == "xmlns" or name == "xmlns":
            continue
        written.add((prefix, "metaId" if local == "metaid" else local))
    return written


#: attributes of a container, which are compared on the elements they concern
_COMPARED_ELSEWHERE: frozenset[tuple[str, str]] = frozenset(
    {
        # `fbc.objective.active`
        ("listOfObjectives", "activeObjective"),
        # `fbc.geneProductAssociation.association`, the infix of gene product ids
        ("geneProductRef", "geneProduct"),
    }
)


@pytest.mark.parametrize("sbml_path", FIXTURE_PARAMS, ids=fixture_idfn)
def test_snapshot_compares_every_attribute(sbml_path: Path) -> None:
    """Test that the comparison reads every attribute libsbml writes.

    An attribute libsbml writes on a compared element, which the comparison does not read, is an attribute whose loss it cannot see. On a core element of the main model only the attributes of the packages are package content.
    """
    doc = comparable_document(_read(sbml_path))
    compared: dict[str, set[str]] = {}
    for (construct, _), attributes in snapshot(doc).items():
        compared.setdefault(construct, set()).update(attributes)
        compared.setdefault(construct.split(".")[0], set()).update(attributes)

    for element in doc.getListOfAllElements():
        written = _written_attributes(element)
        construct = _construct_of(element)
        if construct is not None:
            missing = {local for _, local in written} - compared[construct]
        else:
            # a container, or a core element of the main model: its package
            # attributes only
            missing = {
                local
                for prefix, local in written
                if prefix in ("fbc", "distrib", "comp")
                and local not in compared.get(prefix, set())
                and (element.getElementName(), local) not in _COMPARED_ELSEWHERE
            }
        assert not missing, (
            f"{element.getElementName()} '{element.getIdAttribute()}': "
            f"attributes not compared {sorted(missing)}"
        )


# ---------------------------------------------------------------------------
# the documents compared
# ---------------------------------------------------------------------------
#: the core namespace of an element, which names the level and version
_CORE_NAMESPACE = re.compile(r"http://www\.sbml\.org/sbml/level\d+/version\d+/core")


def _package_content(doc: libsbml.SBMLDocument) -> Counter[str]:
    """Get the package content of a document as the SBML libsbml writes for it.

    This is independent of `snapshot`, which compares a document at L3V2 only, so it can measure a conversion to L3V2. The core namespace an element declares names the level and version of the document and is no content, so it is blanked.

    Args:
        doc: a document, which the caller holds

    Returns:
        how often the SBML of every element of fbc, distrib or comp occurs, and every package attribute of a core element with its value
    """
    content: Counter[str] = Counter()
    for element in doc.getListOfAllElements():
        if element.getPackageName() in PACKAGES:
            content[_CORE_NAMESPACE.sub("core", element.toSBML())] += 1
            continue
        match = _START_TAG.match(element.toSBML())
        assert match is not None, element.toSBML()[:200]
        for name, value in _ATTRIBUTE.findall(match.group(1)):
            prefix, _, _local = name.rpartition(":")
            if prefix in PACKAGES:
                content[f'{element.getElementName()} {name}="{value}"'] += 1
    return content


@pytest.mark.parametrize(
    "sbml_path",
    [
        FBC_ECOLI_CORE_SBML,
        ECOLI_EXPRESSION_SBML,
        FBC_UDC_SBML,
        COMP_ICG_BODY,
        UNCERTAINTY_SBML,
    ],
    ids=fixture_idfn,
)
def test_comparable_document_changes_no_package_content(sbml_path: Path) -> None:
    """Test that the conversion of an L3V1 document to L3V2 changes no content."""
    doc = _read(sbml_path)
    assert (doc.getLevel(), doc.getVersion()) == (3, 1)
    before = _package_content(doc)
    assert before, f"no package content in '{sbml_path}'"

    converted = comparable_document(doc)

    assert (converted.getLevel(), converted.getVersion()) == (3, 2)
    assert (doc.getLevel(), doc.getVersion()) == (3, 1), "the original was converted"
    assert _package_content(converted) == before


@pytest.mark.parametrize(
    "sbml_path, refused",
    [
        # L3V1, which the round trip does not write
        (FBC_ECOLI_CORE_SBML, "L3V1"),
        # L3V2 with fbc version 1, whose flux bounds the walk would never see
        pytest.param(
            testsuite_case("01186"), "fbc version 2", marks=[requires_testsuite]
        ),
    ],
    ids=["L3V1", "fbc-v1"],
)
def test_snapshot_refuses_a_document_which_was_not_converted(
    sbml_path: Path, refused: str
) -> None:
    """Test that a snapshot of a document which was not converted fails loudly.

    A document which is not the one `comparable_document` returns is compared incompletely: an fbc v1 document keeps its content in `fbc:fluxBound` elements, which the walk does not visit, so it would silently report no flux bound at all.
    """
    doc = _read(sbml_path)

    with pytest.raises(ValueError, match=refused):
        snapshot(doc)

    assert snapshot(comparable_document(doc)), "the converted document compares"


@requires_testsuite
def test_fbc_v1_is_compared_as_libsbml_converts_it() -> None:
    """Test that an fbc v1 document is compared as its fbc v2 conversion.

    Each `fbc:fluxBound` becomes a reference to a parameter of the generated id `fb_<reaction>_<operation>`, which carries the value of the bound.
    """
    doc = _read(testsuite_case("01186"))
    fbc_v1: libsbml.FbcModelPlugin = doc.getModel().getPlugin("fbc")
    assert fbc_v1.getPackageVersion() == 1
    flux_bound: libsbml.FluxBound = fbc_v1.getFluxBound(0)
    reaction, operation, value = (
        flux_bound.getReaction(),
        flux_bound.getOperation(),
        flux_bound.getValue(),
    )

    snap = snapshot(comparable_document(doc))

    bound = snap[("fbc.fluxBound", f"model/reaction:{reaction}")]
    side = "lower" if operation == "greaterEqual" else "upper"
    assert bound[f"{side}FluxBound"] == f"fb_{reaction}_{operation}"
    assert bound[f"{side}Value"] == value


def test_roundtrip_document_returns_both_documents(tmp_path: Path) -> None:
    """Test that a round trip returns the document read and the one written."""
    doc_in, doc_out = roundtrip_document(UNCERTAINTY_SBML, tmp_path)

    assert doc_in.getModel() is not None
    assert doc_out.getModel() is not None
    assert (doc_out.getLevel(), doc_out.getVersion()) == (3, 2)
    assert isinstance(structural_diff(doc_in, doc_out), list)


def test_roundtrip_preserves_fbc_strict(tmp_path: Path) -> None:
    """Test that `fbc:strict="true"` of the source survives the round trip.

    `FBC_ECOLI_CORE_SBML` declares `fbc:strict="true"`. `Document.create_sbml`
    used to hardcode `setStrict(False)`, which lost it on every round trip;
    other constructs of this fixture still differ today (gene products and
    the rest of the objective are parsed by a later task), so this only
    asserts on `fbc.strict`, never on an empty diff.
    """
    doc_in, doc_out = roundtrip_document(FBC_ECOLI_CORE_SBML, tmp_path)

    fbc_in: libsbml.FbcModelPlugin = doc_in.getModel().getPlugin("fbc")
    assert fbc_in.getStrict() is True

    diffs = structural_diff(doc_in, doc_out)
    assert [d for d in diffs if d.construct == "fbc.strict"] == []


def _fbc_version(sbml_path: Path) -> int | None:
    """Get the fbc package version a document declares, as libsbml reads it.

    Args:
        sbml_path: path of the SBML file

    Returns:
        the version, `None` for a document which does not declare fbc
    """
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    plugin: libsbml.SBMLDocumentPlugin | None = doc.getPlugin("fbc")
    return plugin.getPackageVersion() if plugin is not None else None


def fbc_v1_cases() -> list[Path]:
    """Get every fbc version 1 case of the vendored SBML test suite.

    The cases are not spelled out: every l3v2 case whose header names an fbc namespace is a candidate, and libsbml decides which version each of them declares.

    Returns:
        the path of every l3v2 case which declares fbc version 1
    """
    candidates: list[Path] = []
    for sbml_path in sorted(SEMANTIC_DIR.glob("*/*-sbml-l3v2.xml")):
        with sbml_path.open(encoding="utf-8") as f:
            if "/fbc/version" in f.read(4000):
                candidates.append(sbml_path)
    return [path for path in candidates if _fbc_version(path) == 1]


@requires_testsuite
def test_roundtrip_of_every_fbc_v1_case_is_valid_and_not_strict(
    tmp_path: Path,
) -> None:
    """Test that an fbc v1 case round trips to a valid document which is not strict.

    fbc version 1 has no `fbc:strict` attribute, so such a source says nothing about strictness, but libsbml's `convert fbc v1 to fbc v2` converter sets `fbc:strict="true"` on every one of them. Under that claim the `constant="false"` species references these models use are an error, libsbml 2020714, and 11 of the 12 cases are valid as they are and invalid as converted, with 54 errors each. The round trip therefore writes `fbc:strict="false"`, the weakest claim, rather than agreeing with the converter: a round trip must never turn a valid model into an invalid one (ruling T5c).
    """
    cases = fbc_v1_cases()
    assert cases, "no fbc version 1 case in the vendored SBML test suite"

    invalid: list[str] = []
    strict: list[str] = []
    for sbml_path in cases:
        _doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
        result = validate_doc(
            doc_out, options=ValidationOptions(units_consistency=False)
        )
        if not result.is_valid():
            ids = sorted({error.getErrorId() for error in result.errors})
            invalid.append(f"{sbml_path.name}: {result.error_count} errors {ids}")
        fbc_out: libsbml.FbcModelPlugin = doc_out.getModel().getPlugin("fbc")
        if fbc_out.getStrict():
            strict.append(sbml_path.name)

    assert invalid == []
    assert strict == []


@requires_testsuite
def test_structural_diff_does_not_compare_fbc_strict_of_an_fbc_v1_source() -> None:
    """Test that the `fbc:strict` libsbml's converter invents is compared on no side.

    The `fbc:strict="true"` of a converted fbc v1 document is the invention of the converter, not content of the source, so neither side is held to it; for an fbc v2 source the same damage is reported as ever, which the `flip_strict` mutation of `MUTATIONS` covers. Nothing else of an fbc v1 source is skipped, which the damaged flux bound at the end shows.
    """
    source = _read(testsuite_case("01186"))
    converted = comparable_document(source)
    assert converted is not source
    plugin: libsbml.FbcModelPlugin = converted.getModel().getPlugin("fbc")
    assert plugin.getStrict() is True, "the converter invents fbc:strict"

    assert plugin.setStrict(False) == libsbml.LIBSBML_OPERATION_SUCCESS

    assert structural_diff(source, converted) == []

    reaction: libsbml.Reaction = converted.getModel().getReaction("R01")
    reaction_fbc: libsbml.FbcReactionPlugin = reaction.getPlugin("fbc")
    assert reaction_fbc.setUpperFluxBound("fb_R02_lessEqual") == (
        libsbml.LIBSBML_OPERATION_SUCCESS
    )

    differences = structural_diff(source, converted)

    # the bound of that one reaction, by its id and by the value it points at
    assert {(d.construct, d.element_id) for d in differences} == {
        ("fbc.fluxBound", "model/reaction:R01")
    }
    assert sorted(d.attribute for d in differences) == ["upperFluxBound", "upperValue"]


# ---------------------------------------------------------------------------
# the package round trip
# ---------------------------------------------------------------------------
#: the construct census of a fixture and the package differences of its round trip
Comparison = tuple[Counter[str], list[Difference]]


@pytest.fixture(scope="module")
def package_roundtrip(
    tmp_path_factory: pytest.TempPathFactory,
) -> Callable[[Path], Comparison]:
    """Round trip a fixture and compare its package content, once per fixture.

    The tests below assert on one construct of a fixture each, and the round trip of `FBC_RECON3D_SBML` takes about ten seconds, so every fixture is round tripped once and its result is cached for the module. The differences come from `snapshots`, which is the comparison policy, and the census which proves a fixture has a construct is an independent recount of the same document. The cache holds plain values only: the documents are released when the comparison returns, and a libsbml object does not keep its document alive.

    Args:
        tmp_path_factory: pytest's factory of the directory the round trips write to

    Returns:
        a function which round trips an SBML file and returns how many elements of every construct libsbml reads from it, counted independently of `snapshot`, and every difference of its package content, of every package; a test which is about one package filters by it, and `_assert_preserved` filters by construct
    """
    tmp_path = tmp_path_factory.mktemp("package-roundtrip")
    cache: dict[Path, Comparison] = {}

    def compare(sbml_path: Path) -> Comparison:
        if sbml_path not in cache:
            doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
            cache[sbml_path] = (
                _expected_constructs(comparable_document(doc_in)),
                diff_snapshots(*snapshots(doc_in, doc_out)),
            )
        return cache[sbml_path]

    return compare


def _assert_preserved(comparison: Comparison, *constructs: str) -> None:
    """Assert that a fixture has each construct and that the round trip changes none.

    Args:
        comparison: the census and the differences of a fixture, see `package_roundtrip`
        constructs: the constructs which have to be preserved
    """
    counts, differences = comparison
    assert [c for c in constructs if not counts[c]] == [], (
        f"the fixture has none of these constructs, so preserving them says "
        f"nothing: {[c for c in constructs if not counts[c]]}"
    )
    assert [str(d) for d in differences if d.construct in constructs] == []


def test_roundtrip_preserves_gene_products(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the gene products of a model and its associations survive a round trip.

    `FBC_ECOLI_CORE_SBML` has 137 gene products, every one of them annotated, and 69 reactions with a gene product association.
    """
    counts, _ = package_roundtrip(FBC_ECOLI_CORE_SBML)
    assert counts["fbc.geneProduct"] == 137
    assert counts["fbc.geneProductAssociation"] == 69

    _assert_preserved(
        package_roundtrip(FBC_ECOLI_CORE_SBML),
        "fbc.geneProduct",
        "fbc.geneProductAssociation",
    )


#: the sboTerm an `and` and an `or` node of a gene product association carries
#: in the two e_coli_core fixtures of `resources/distrib`; each of the two
#: restates the operator of the node it sits on, SBO:0000173 is `and` and
#: SBO:0000174 is `or`
ASSOCIATION_NODE_SBO: dict[str, str] = {"and": "SBO:0000173", "or": "SBO:0000174"}


@pytest.mark.parametrize(
    "sbml_path",
    [ECOLI_CORE_DISTRIB_SBML, ECOLI_EXPRESSION_SBML],
    ids=fixture_idfn,
)
def test_roundtrip_loses_only_the_sboterm_of_an_association_node(
    sbml_path: Path, tmp_path: Path
) -> None:
    """Test that a round trip loses no more of an association than the sboTerm of a node.

    `Reaction.geneProductAssociation` holds an association as the infix string
    of its gene product ids, and a string cannot hold what a node of the
    association carries: `tests/structural.py` therefore compares the metadata
    of every `and`, `or` and `geneProductRef` node as `nodes`, apart from the
    string. The two e_coli_core fixtures of `resources/distrib` are the only
    documents of the corpus whose nodes carry any, and this is the loss that
    is left; it is not whitelisted, it is pinned here.

    What is lost has to stay exactly this: an `sboTerm` on an `and` or an `or`
    node which restates the operator of that node, so the infix string loses
    nothing which is not derivable from it. Any other metadata on a node - a
    metaid, an annotation, notes, another term, or anything at all on a
    `geneProductRef` - would be a real loss and fails this test, and so does a
    changed association string, which is asserted literally rather than left
    to the whitelist.
    """
    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
    census = _expected_constructs(comparable_document(doc_in))
    assert census["fbc.geneProductAssociation"] == 69

    differences = [d for d in structural_diff(doc_in, doc_out) if d.package == "fbc"]

    assert {(d.construct, d.attribute) for d in differences} == {
        ("fbc.geneProductAssociation", "nodes")
    }
    assert len(differences) == 42
    kinds: Counter[str] = Counter()
    for difference in differences:
        reaction_id = difference.element_id.removeprefix("model/reaction:")
        assert _association(doc_in, reaction_id) == _association(doc_out, reaction_id)
        assert difference.after == (), difference
        assert isinstance(difference.before, tuple)
        for element, gene_product, metadata in difference.before:
            sid, name, meta_id, sbo_term, cvterms, notes = metadata
            assert element in ASSOCIATION_NODE_SBO, difference
            assert sbo_term == ASSOCIATION_NODE_SBO[element], difference
            assert (sid, name, meta_id, cvterms, notes) == (None, None, None, (), None)
            assert gene_product == "", difference
            kinds[element] += 1

    assert kinds == Counter({"or": 32, "and": 22})


def test_roundtrip_preserves_objectives(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the objective of a model and its flux objectives survive a round trip.

    `FBC_ECOLI_CORE_SBML` maximizes the biomass reaction, which is the one thing an FBA model is run for.
    """
    counts, _ = package_roundtrip(FBC_ECOLI_CORE_SBML)
    assert counts["fbc.objective"] == 1
    assert counts["fbc.fluxObjective"] == 1

    _assert_preserved(
        package_roundtrip(FBC_ECOLI_CORE_SBML), "fbc.objective", "fbc.fluxObjective"
    )


def _objectives_model(active: str | None) -> Model:
    """Get a model with two objectives, of which `active` is the active one.

    Args:
        active: the id of the objective which is the `activeObjective`, `None` for a model whose objectives are all inactive

    Returns:
        the model definition
    """
    return Model(
        sid="two_objectives",
        packages=[Package.FBC_V2],
        compartments=[Compartment(sid="c", value=1.0)],
        species=[Species(sid="S1", compartment="c", initialAmount=1.0)],
        reactions=[Reaction(sid="R1", equation="S1 ->")],
        objectives=[
            Objective(
                sid=sid,
                objectiveType=objective_type,
                active=sid == active,
                fluxObjectives={"R1": 1.0},
            )
            for sid, objective_type in [("obj1", "maximize"), ("obj2", "minimize")]
        ],
    )


@pytest.mark.parametrize("active", ["obj1", "obj2", None])
def test_roundtrip_keeps_the_active_objective(
    active: str | None, tmp_path: Path
) -> None:
    """Test that the `activeObjective` of a model with two objectives is the one read.

    `Objective.create_sbml` writes the objectives in order and sets the model's `activeObjective` for each one whose `active` is set, so the last active objective written wins. The parser therefore has to read the `activeObjective` of the document and set `active` on that objective only: without it every objective is active, which makes the *last* one the active one, and a model whose first objective is the active one comes back optimizing the wrong thing. A model without an active objective keeps none.
    """
    sbml_path = _source_path(lambda: _objectives_model(active), tmp_path)
    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)

    objectives: libsbml.ListOfObjectives = _fbc(doc_in).getListOfObjectives()
    assert [o.getIdAttribute() for o in objectives] == ["obj1", "obj2"]
    assert objectives.isSetActiveObjective() is (active is not None)
    assert not objectives.isSetActiveObjective() or (
        objectives.getActiveObjective() == active
    )

    diffs = [d for d in structural_diff(doc_in, doc_out) if d.package == "fbc"]

    assert [str(d) for d in diffs] == []


def test_roundtrip_preserves_bounds_charge_and_formula(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the flux bounds, charges and chemical formulas of a model survive.

    The flux bounds of `FBC_ECOLI_CORE_SBML` are what makes its flux space finite; 72 of its 72 species carry a charge and a chemical formula.
    """
    counts, _ = package_roundtrip(FBC_ECOLI_CORE_SBML)
    assert counts["fbc.fluxBound"] == 95
    assert counts["fbc.charge"] == 72
    assert counts["fbc.chemicalFormula"] == 72

    _assert_preserved(
        package_roundtrip(FBC_ECOLI_CORE_SBML),
        "fbc.fluxBound",
        "fbc.charge",
        "fbc.chemicalFormula",
    )


def _charge_sbml(tmp_path: Path, fbc_version: int, charges: list[float]) -> Path:
    """Write a model whose species carry the given charges, with libsbml.

    The source is built with libsbml rather than with the factory, so that the
    charges of the document read are the ones stated here and not the ones the
    writer under test would have produced; a writer which loses a charge would
    otherwise lose it on both sides and the comparison would see nothing. One
    species carries no charge at all, so that an unset charge is not confused
    with a charge of zero.

    Args:
        tmp_path: the directory the SBML file is written to
        fbc_version: the fbc package version of the document, 2 or 3
        charges: the charge of each species of the model, in order

    Returns:
        the path of the SBML file
    """
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(
        libsbml.SBMLNamespaces(3, 2, "fbc", fbc_version)
    )
    doc.setPackageRequired("fbc", False)
    model: libsbml.Model = doc.createModel()
    model.setId(f"charge_fbc_v{fbc_version}")
    model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
    model_fbc.setStrict(False)
    compartment: libsbml.Compartment = model.createCompartment()
    compartment.setId("c")
    compartment.setConstant(True)
    compartment.setSize(1.0)
    compartment.setSpatialDimensions(3.0)
    for index, charge in enumerate([*charges, None]):
        species: libsbml.Species = model.createSpecies()
        species.setId(f"S{index}")
        species.setCompartment("c")
        species.setConstant(False)
        species.setBoundaryCondition(False)
        species.setHasOnlySubstanceUnits(False)
        species.setInitialAmount(1.0)
        if charge is None:
            continue
        plugin: libsbml.FbcSpeciesPlugin = species.getPlugin("fbc")
        value = float(charge) if fbc_version >= 3 else int(charge)
        assert plugin.setCharge(value) == libsbml.LIBSBML_OPERATION_SUCCESS

    sbml_path = tmp_path / f"charge_fbc_v{fbc_version}.xml"
    libsbml.writeSBMLToFile(doc, str(sbml_path))
    return sbml_path


def _charges(doc: libsbml.SBMLDocument) -> list[float | None]:
    """Get the charge of every species of a document, as libsbml writes it.

    The fbc version decides which of the two getters carries the charge, and
    this test reads it without `structural._charge`, which does the same
    dispatch, on purpose: the test checks what the comparison reports, so a
    defect in that dispatch has to be able to fail it rather than cancel out
    on both sides.

    Args:
        doc: the document, which the caller holds

    Returns:
        the charge of every species in document order, `None` for a species
        without one
    """
    charges: list[float | None] = []
    species: libsbml.Species
    for species in doc.getModel().getListOfSpecies():
        plugin: libsbml.FbcSpeciesPlugin = species.getPlugin("fbc")
        if not plugin.isSetCharge():
            charges.append(None)
        elif plugin.getPackageVersion() >= 3:
            charges.append(float(plugin.getChargeAsDouble()))
        else:
            charges.append(float(plugin.getCharge()))
    return charges


@pytest.mark.parametrize(
    "fbc_version, charges",
    [
        (2, [-2.0, 0.0, 3.0]),
        # fbc version 3 has a double charge, which need not be a whole number
        (3, [-2.5, 0.0, 3.0, -2.0]),
    ],
    ids=["fbc-v2", "fbc-v3"],
)
def test_roundtrip_preserves_the_charge_of_each_fbc_version(
    fbc_version: int, charges: list[float], tmp_path: Path
) -> None:
    """Test that the charge of a species survives a round trip in both fbc versions.

    libsbml keeps the integer `fbc:charge` of fbc version 2 and the double
    `fbc:charge` of fbc version 3 apart and writes only the one of the version
    of the document, so a charge set as the wrong python type comes out as
    `fbc:charge="0"`. A charge of zero and a species without a charge stay
    apart, which the last species of the fixture, which has none, shows.
    """
    sbml_path = _charge_sbml(tmp_path, fbc_version, charges)
    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
    assert _charges(doc_in) == [*charges, None]
    assert _expected_constructs(comparable_document(doc_in))["fbc.charge"] == len(
        charges
    )

    diffs = [d for d in structural_diff(doc_in, doc_out) if d.package == "fbc"]

    assert [str(d) for d in diffs] == []
    assert _charges(doc_out) == [*charges, None]


def _one_flux_bound_model() -> Model:
    """Get a model whose reaction states its lower flux bound and no upper one.

    A strict model needs both bounds on every reaction, so the model is not strict; fbc version 2, where a bound is a parameter the reaction references.

    Returns:
        the model definition
    """
    return Model(
        sid="one_flux_bound",
        packages=[Package.FBC_V2],
        strict=False,
        compartments=[Compartment(sid="c", value=1.0)],
        species=[Species(sid="S1", compartment="c", initialAmount=1.0)],
        parameters=[Parameter(sid="lb", value=-10.0, constant=True)],
        reactions=[Reaction(sid="R1", equation="S1 ->", lowerFluxBound="lb")],
    )


def test_roundtrip_keeps_a_reaction_with_one_flux_bound(tmp_path: Path) -> None:
    """Test that a reaction with one of the two flux bounds keeps it, and gains no other.

    Both bounds of a reaction are optional on their own in a model which is not strict, and the two are read and written one by one, so a reaction can state one and not the other. The bound it states survives, and the one it does not state is not invented.
    """
    sbml_path = _source_path(_one_flux_bound_model, tmp_path)
    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
    reaction_in: libsbml.FbcReactionPlugin = (
        doc_in.getModel().getReaction("R1").getPlugin("fbc")
    )
    assert reaction_in.getLowerFluxBound() == "lb"
    assert reaction_in.isSetUpperFluxBound() is False

    diffs = [d for d in structural_diff(doc_in, doc_out) if d.package == "fbc"]

    assert [str(d) for d in diffs] == []
    reaction_out: libsbml.FbcReactionPlugin = (
        doc_out.getModel().getReaction("R1").getPlugin("fbc")
    )
    assert reaction_out.getLowerFluxBound() == "lb"
    assert reaction_out.isSetUpperFluxBound() is False


@requires_testsuite
def test_roundtrip_preserves_fbc_v1_flux_bounds(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the flux bounds of an fbc version 1 document survive a round trip.

    fbc version 1 states a bound as an `fbc:fluxBound` element of the model rather than as a parameter the reaction references, and there is no `Model` field for that element. The parser converts an fbc version 1 document with libsbml's own `convert fbc v1 to fbc v2` converter before reading it, which is exactly how `tests/structural.py` compares such a document: every bound becomes a parameter of the generated id `fb_<reaction>_<operation>`, which the reaction references.
    """
    sbml_path = testsuite_case("01186")
    doc = _read(sbml_path)
    fbc_v1: libsbml.FbcModelPlugin = doc.getModel().getPlugin("fbc")
    assert fbc_v1.getPackageVersion() == 1
    assert fbc_v1.getNumFluxBounds() == 52

    counts, _ = package_roundtrip(sbml_path)
    assert counts["fbc.fluxBound"] == 26

    _assert_preserved(package_roundtrip(sbml_path), "fbc.fluxBound")


def test_roundtrip_preserves_user_defined_constraints(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the user-defined constraints of a model survive a round trip.

    A user-defined constraint is an fbc version 3 constraint which is not implied by the stoichiometry of the network; `FBC_UDC_SBML` is the only fixture of the repository which has any.
    """
    counts, _ = package_roundtrip(FBC_UDC_SBML)
    assert counts["fbc.userDefinedConstraint"] == 2
    assert counts["fbc.userDefinedConstraintComponent"] == 4

    _assert_preserved(
        package_roundtrip(FBC_UDC_SBML),
        "fbc.userDefinedConstraint",
        "fbc.userDefinedConstraintComponent",
    )


def _no_variable_type_sbml(tmp_path: Path) -> Path:
    """Write an fbc v3 model whose flux objective and constraint component have no `variableType`.

    `fbc:variableType` was added in fbc version 3 and is optional, so a document of that version can omit it; libsbml reads such an element with `isSetVariableType() == False`. The document is built with libsbml rather than with the factory, so that it states exactly that and nothing the writer decides.

    Args:
        tmp_path: the directory the SBML file is written to

    Returns:
        the path of the SBML file
    """
    namespaces = libsbml.SBMLNamespaces(3, 1, "fbc", 3)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(namespaces)
    doc.setPackageRequired("fbc", False)
    model: libsbml.Model = doc.createModel()
    model.setId("no_variable_type")
    model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
    model_fbc.setStrict(False)
    compartment: libsbml.Compartment = model.createCompartment()
    compartment.setId("c")
    compartment.setConstant(True)
    compartment.setSize(1.0)
    compartment.setSpatialDimensions(3.0)
    species: libsbml.Species = model.createSpecies()
    species.setId("S1")
    species.setCompartment("c")
    species.setConstant(False)
    species.setBoundaryCondition(False)
    species.setHasOnlySubstanceUnits(False)
    species.setInitialAmount(1.0)
    for pid, value in (("lb", 0.0), ("ub", 10.0), ("coef", 1.0)):
        parameter: libsbml.Parameter = model.createParameter()
        parameter.setId(pid)
        parameter.setValue(value)
        parameter.setConstant(True)
    reaction: libsbml.Reaction = model.createReaction()
    reaction.setId("R1")
    reaction.setReversible(False)
    reaction.setFast(False)
    reactant: libsbml.SpeciesReference = reaction.createReactant()
    reactant.setSpecies("S1")
    reactant.setStoichiometry(1.0)
    reactant.setConstant(True)
    objective: libsbml.Objective = model_fbc.createObjective()
    objective.setId("obj")
    objective.setType("maximize")
    model_fbc.setActiveObjectiveId("obj")
    flux_objective: libsbml.FluxObjective = objective.createFluxObjective()
    flux_objective.setReaction("R1")
    flux_objective.setCoefficient(1.0)
    constraint: libsbml.UserDefinedConstraint = model_fbc.createUserDefinedConstraint()
    constraint.setLowerBound("lb")
    constraint.setUpperBound("ub")
    component: libsbml.UserDefinedConstraintComponent = (
        constraint.createUserDefinedConstraintComponent()
    )
    component.setVariable("R1")
    component.setCoefficient("coef")

    sbml_path = tmp_path / "no_variable_type.xml"
    libsbml.writeSBMLToFile(doc, str(sbml_path))
    return sbml_path


def test_roundtrip_keeps_an_unset_variable_type_unset(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that an element read without a `variableType` is written without one.

    fbc version 3 requires `fbc:variableType` on a flux objective and on a constraint component, so a document without one is invalid; a parser reads what is there and does not repair it, so the element must not be given the `linear` of the default and the writer must not try to set what the `Model` does not have. `UserDefinedConstraintComponent.create_sbml` routes `setVariableType` through `check()`, which logged two errors per component for the value the parser used to pass for "no variable type".

    Reading the invalid source logs libsbml's own consistency errors about the missing attribute, which are about the source. The assertion is therefore on the errors `check()` reports for a libsbml call which failed, which is what the writer produced here.
    """
    sbml_path = _no_variable_type_sbml(tmp_path)

    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)

    fbc_out: libsbml.FbcModelPlugin = doc_out.getModel().getPlugin("fbc")
    flux_objective: libsbml.FluxObjective = fbc_out.getObjective(0).getFluxObjective(0)
    component: libsbml.UserDefinedConstraintComponent = (
        fbc_out.getUserDefinedConstraint(0).getUserDefinedConstraintComponent(0)
    )
    assert flux_objective.isSetVariableType() is False
    assert component.isSetVariableType() is False

    assert [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.ERROR
        and "Error encountered trying to" in record.getMessage()
    ] == []
    assert [
        str(d) for d in structural_diff(doc_in, doc_out) if d.package == "fbc"
    ] == []


def test_roundtrip_preserves_key_value_pairs(tmp_path: Path) -> None:
    """Test that the fbc key-value pairs of a model survive a round trip.

    A key-value pair of fbc version 3 sits on any element; `FBC_KVP_SBML` puts three of them on a parameter, each with a key, a value and a uri.
    """
    doc_in, doc_out = roundtrip_document(FBC_KVP_SBML, tmp_path)
    assert _expected_constructs(comparable_document(doc_in))["fbc.keyValuePair"] == 3

    diffs = [d for d in structural_diff(doc_in, doc_out) if d.package == "fbc"]

    assert [str(d) for d in diffs] == []


def _speciesref_kvp_model() -> Model:
    """Get a model whose reactant, product and modifier each carry a key-value pair.

    A species reference is an `SBase` and carries the key-value pairs of fbc
    version 3 like any other element; `EquationPart` holds them for all three
    roles, a `ModifierSpeciesReference` included.

    Returns:
        the model definition
    """
    return Model(
        sid="speciesref_key_value_pair",
        packages=[Package.FBC_V3],
        strict=False,
        compartments=[Compartment(sid="c", value=1.0)],
        species=[
            Species(sid=sid, compartment="c", initialAmount=1.0)
            for sid in ("S1", "S2", "M1")
        ],
        reactions=[
            Reaction(
                sid="R1",
                equation=ReactionEquation(
                    reactants=[
                        EquationPart(
                            species="S1",
                            stoichiometry=1.0,
                            keyValuePairs=[
                                KeyValuePair(
                                    key="reactant-key",
                                    value="47",
                                    uri="https://example.org/keys",
                                )
                            ],
                        )
                    ],
                    products=[
                        EquationPart(
                            species="S2",
                            stoichiometry=1.0,
                            keyValuePairs=[
                                KeyValuePair(key="product-key", value="48", uri=None)
                            ],
                        )
                    ],
                    modifiers=[
                        EquationPart(
                            species="M1",
                            keyValuePairs=[
                                KeyValuePair(key="modifier-key", value="49", uri=None)
                            ],
                        )
                    ],
                    reversible=False,
                ),
            )
        ],
    )


#: the `key` of a `keyValuePair` element, as libsbml writes it
_KEY_ATTRIBUTE = re.compile(r"<keyValuePair[^>]*\skey=\"([^\"]*)\"")


def _written_keys(sbml_path: Path) -> set[str]:
    """Get the key of every key-value pair of an SBML file, from its text.

    The keys are read from the file rather than through libsbml, which does
    not read back the pairs of a reactant or a product, see
    `test_libsbml_reads_the_key_value_pairs_of_a_modifier_only`.

    Args:
        sbml_path: path of the SBML file

    Returns:
        the key of every `keyValuePair` element of the file
    """
    return set(_KEY_ATTRIBUTE.findall(sbml_path.read_text(encoding="utf-8")))


def test_roundtrip_preserves_key_value_pairs_of_a_species_reference(
    tmp_path: Path,
) -> None:
    """Test that the key-value pairs of a species reference survive a round trip.

    `EquationPart.keyValuePairs` was declared and never written, so a reactant,
    product or modifier lost its pairs on the way into SBML. All three are
    written now, which the file of the fixture shows; of the three libsbml
    reads only the one of the modifier back, so that is the one whose round
    trip can be compared, and the census of the document read is what says so.
    """
    sbml_path = _source_path(_speciesref_kvp_model, tmp_path)
    assert _written_keys(sbml_path) == {"reactant-key", "product-key", "modifier-key"}

    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
    assert _expected_constructs(comparable_document(doc_in))["fbc.keyValuePair"] == 1, (
        "libsbml reads the key-value pairs of the modifier only, see "
        "`test_libsbml_reads_the_key_value_pairs_of_a_modifier_only`; a count "
        "of 3 means the defect is fixed, so compare all three pairs here and "
        "drop the test of the defect"
    )

    diffs = [d for d in structural_diff(doc_in, doc_out) if d.package == "fbc"]

    assert [str(d) for d in diffs] == []
    modifier: libsbml.ModifierSpeciesReference = (
        doc_out.getModel().getReaction("R1").getModifier(0)
    )
    plugin: libsbml.FbcSBasePlugin = modifier.getPlugin("fbc")
    pair: libsbml.KeyValuePair = plugin.getKeyValuePair(0)
    assert (pair.getKey(), pair.getValue()) == ("modifier-key", "49")


def test_libsbml_reads_the_key_value_pairs_of_a_modifier_only(tmp_path: Path) -> None:
    """Test the libsbml defect which hides the key-value pairs of a reactant or product.

    libsbml 5.21.2 writes the `listOfKeyValuePairs` annotation of fbc version 3
    on a `speciesReference` and never reads it back; on a
    `modifierSpeciesReference` it reads it as it should. The pairs are in the
    file either way, which `_written_keys` shows, so nothing is lost on the way
    out; they are lost on the way back in, inside libsbml, before any code of
    this package sees them. This is why the round trip of a reactant or product
    pair cannot be compared and why `structural_diff` reports nothing for it:
    the comparison sees what libsbml reads, see the docstring of
    `tests/structural.py`.

    The document is built with libsbml alone, so that the defect is pinned
    where it lives rather than through the factory.
    """
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(
        libsbml.SBMLNamespaces(3, 2, "fbc", 3)
    )
    doc.setPackageRequired("fbc", False)
    model: libsbml.Model = doc.createModel()
    model.setId("libsbml_key_value_pairs")
    model_fbc: libsbml.FbcModelPlugin = model.getPlugin("fbc")
    model_fbc.setStrict(False)
    compartment: libsbml.Compartment = model.createCompartment()
    compartment.setId("c")
    compartment.setConstant(True)
    for sid in ("A", "M"):
        species: libsbml.Species = model.createSpecies()
        species.setId(sid)
        species.setCompartment("c")
        species.setConstant(False)
        species.setBoundaryCondition(False)
        species.setHasOnlySubstanceUnits(False)
    reaction: libsbml.Reaction = model.createReaction()
    reaction.setId("R1")
    reaction.setReversible(False)
    reactant: libsbml.SpeciesReference = reaction.createReactant()
    reactant.setSpecies("A")
    reactant.setStoichiometry(1.0)
    reactant.setConstant(True)
    modifier: libsbml.ModifierSpeciesReference = reaction.createModifier()
    modifier.setSpecies("M")
    for sref, key in ((reactant, "reactant-key"), (modifier, "modifier-key")):
        plugin: libsbml.FbcSBasePlugin = sref.getPlugin("fbc")
        pairs: libsbml.ListOfKeyValuePairs = plugin.getListOfKeyValuePairs()
        pairs.setXmlns("http://sbml.org/fbc/keyvaluepair")
        pair: libsbml.KeyValuePair = pairs.createKeyValuePair()
        assert pair.setKey(key) == libsbml.LIBSBML_OPERATION_SUCCESS
        assert pair.setValue("1") == libsbml.LIBSBML_OPERATION_SUCCESS

    sbml_path = tmp_path / "libsbml_key_value_pairs.xml"
    assert libsbml.writeSBMLToFile(doc, str(sbml_path))
    assert _written_keys(sbml_path) == {"reactant-key", "modifier-key"}

    doc_again: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    reaction_again: libsbml.Reaction = doc_again.getModel().getReaction("R1")
    reactant_plugin: libsbml.FbcSBasePlugin = reaction_again.getReactant(0).getPlugin(
        "fbc"
    )
    modifier_plugin: libsbml.FbcSBasePlugin = reaction_again.getModifier(0).getPlugin(
        "fbc"
    )
    assert reactant_plugin.getNumKeyValuePairs() == 0, (
        "libsbml reads the key-value pairs of a species reference now, so the "
        "defect this test pins is fixed: delete this test and compare all "
        "three pairs in "
        "`test_roundtrip_preserves_key_value_pairs_of_a_species_reference`"
    )
    assert modifier_plugin.getNumKeyValuePairs() == 1


#: every fbc fixture of the repository whose content round trips unchanged,
#: with the constructs it has to contain
FBC_FIXTURES: list[tuple[Path, tuple[str, ...]]] = [
    (
        FBC_ECOLI_CORE_SBML,
        (
            "fbc.package",
            "fbc.strict",
            "fbc.geneProduct",
            "fbc.geneProductAssociation",
            "fbc.fluxBound",
            "fbc.charge",
            "fbc.chemicalFormula",
            "fbc.objective",
            "fbc.fluxObjective",
        ),
    ),
    (
        FBC_RECON3D_SBML,
        (
            "fbc.package",
            "fbc.strict",
            "fbc.geneProduct",
            "fbc.geneProductAssociation",
            "fbc.fluxBound",
            "fbc.charge",
            "fbc.chemicalFormula",
            "fbc.objective",
            "fbc.fluxObjective",
        ),
    ),
    (
        FBC_UDC_SBML,
        (
            "fbc.package",
            "fbc.strict",
            "fbc.userDefinedConstraint",
            "fbc.userDefinedConstraintComponent",
        ),
    ),
]


@pytest.mark.parametrize(
    "sbml_path, constructs",
    FBC_FIXTURES,
    ids=[sbml_path.name for sbml_path, _ in FBC_FIXTURES],
)
def test_roundtrip_preserves_the_whole_fbc_content(
    sbml_path: Path,
    constructs: tuple[str, ...],
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that a round trip of an fbc fixture changes no fbc content at all.

    Between them the three fixtures carry every fbc construct the parser reads: `FBC_RECON3D_SBML` is the largest model of the repository with 2248 gene products, 10600 flux bounds and 5835 charges, and `FBC_UDC_SBML` is the only one with user-defined constraints. This asserts on every fbc difference, not on the named constructs only, so an fbc construct the round trip *adds* fails it too.
    """
    counts, differences = package_roundtrip(sbml_path)
    assert [c for c in constructs if not counts[c]] == []

    assert [str(d) for d in differences if d.package == "fbc"] == []


# ---------------------------------------------------------------------------
# the whitelist, ruling R5
# ---------------------------------------------------------------------------
def _normalization(name: str) -> Normalization:
    """Get a whitelist entry by name."""
    (entry,) = [entry for entry in WHITELIST if entry.name == name]
    return entry


def test_whitelist_is_exactly_ruling_r5() -> None:
    """Test that the whitelist holds the three normalizations of R5, each with a reason.

    A whitelist is where a real loss hides, so an entry is added by a ruling, never on the way.
    """
    assert [(entry.name, entry.construct, entry.attribute) for entry in WHITELIST] == [
        ("gpa-flattening", "fbc.geneProductAssociation", "association"),
        ("cn-integer", None, "math"),
        ("identifiers-org", None, "cvterms"),
    ]
    for entry in WHITELIST:
        assert len(entry.reason) > 40, entry.name


def test_whitelist_applies_to_the_construct_of_its_entry() -> None:
    """Test that an entry is keyed by its construct and attribute, not by the attribute.

    The GPA flattening is a normalization of an `fbc.geneProductAssociation`; another construct with an attribute of the same name must not inherit it.
    """
    nested: Attributes = {"association": "((a and b) and c)"}
    flattened: Attributes = {"association": "(a and b and c)"}
    gpa, port = "fbc.geneProductAssociation", "comp.port"
    before: Snapshot = {
        (gpa, "model/reaction:R1"): nested,
        (port, "model/port:p"): nested,
    }
    after: Snapshot = {
        (gpa, "model/reaction:R1"): flattened,
        (port, "model/port:p"): flattened,
    }

    differences = diff_snapshots(before, after)

    assert [(d.construct, d.element_id, d.attribute) for d in differences] == [
        (port, "model/port:p", "association")
    ]


def _parsed_again(doc: libsbml.SBMLDocument, infix: str) -> str:
    """Parse an association by its gene product ids and write it again.

    Args:
        doc: the document whose gene products the association references, which the caller holds
        infix: the association as an infix string of gene product ids

    Returns:
        the infix string libsbml writes for it
    """
    association: libsbml.FbcAssociation = (
        libsbml.FbcAssociation.parseFbcInfixAssociation(infix, _fbc(doc), True, False)
    )
    result: str = association.toInfix(True)
    return result


def _evaluate(infix: str, genes: dict[str, bool]) -> bool:
    """Evaluate an association for the given state of every gene."""
    return bool(eval(infix, {"__builtins__": {}}, genes))


#: the associations of e_coli_core which libsbml does not write back as read,
#: as the source states them
NESTED: dict[str, str] = {
    "R_PFL": (
        "(((G_b0902 and G_b0903) and G_b2579) or (G_b0902 and G_b0903) or "
        "(G_b0902 and G_b3114) or (G_b3951 and G_b3952))"
    ),
    "R_ATPS4r": (
        "(((G_b3736 and G_b3737 and G_b3738) and (G_b3731 and G_b3732 and "
        "G_b3733 and G_b3734 and G_b3735)) or ((G_b3736 and G_b3737 and "
        "G_b3738) and (G_b3731 and G_b3732 and G_b3733 and G_b3734 and "
        "G_b3735) and G_b3739))"
    ),
}

#: the associations of e_coli_core which libsbml does not write back as read,
#: with the form it writes them in
FLATTENED: dict[str, str] = {
    "R_PFL": (
        "((G_b0902 and G_b0903 and G_b2579) or (G_b0902 and G_b0903) or "
        "(G_b0902 and G_b3114) or (G_b3951 and G_b3952))"
    ),
    "R_ATPS4r": (
        "((G_b3736 and G_b3737 and G_b3738 and G_b3731 and G_b3732 and G_b3733 and "
        "G_b3734 and G_b3735) or (G_b3736 and G_b3737 and G_b3738 and G_b3731 and "
        "G_b3732 and G_b3733 and G_b3734 and G_b3735 and G_b3739))"
    ),
}


def _association(doc: libsbml.SBMLDocument, reaction_id: str) -> str:
    """Get the association of a reaction by its gene product ids, the document is held."""
    reaction: libsbml.Reaction = doc.getModel().getReaction(reaction_id)
    plugin: libsbml.FbcReactionPlugin = reaction.getPlugin("fbc")
    infix: str = plugin.getGeneProductAssociation().getAssociation().toInfix(True)
    return infix


def test_gpa_flattening_pins_every_association_libsbml_changes() -> None:
    """Test that R_PFL and R_ATPS4r are the associations of e_coli_core libsbml changes."""
    doc = _read(FBC_ECOLI_CORE_SBML)
    changed: list[str] = []
    for reaction in doc.getModel().getListOfReactions():
        if not reaction.getPlugin("fbc").isSetGeneProductAssociation():
            continue
        association = _association(doc, reaction.getIdAttribute())
        if _parsed_again(doc, association) != association:
            changed.append(reaction.getIdAttribute())

    assert changed == list(FLATTENED)


@pytest.mark.parametrize("reaction_id", FLATTENED)
def test_gpa_flattening_is_what_libsbml_does_and_means_the_same(
    reaction_id: str,
) -> None:
    """Test the GPA flattening against libsbml, and that it preserves the boolean rule."""
    doc = _read(FBC_ECOLI_CORE_SBML)
    association = _association(doc, reaction_id)
    flattened = _parsed_again(doc, association)
    assert flattened == FLATTENED[reaction_id]
    assert _normalization("gpa-flattening").equivalent(association, flattened)

    genes = sorted(set(re.findall(r"G_\w+", association)))
    for state in product([False, True], repeat=len(genes)):
        assignment = dict(zip(genes, state, strict=True))
        assert _evaluate(association, assignment) == _evaluate(flattened, assignment)


def test_roundtrip_flattens_exactly_the_two_pinned_associations(
    tmp_path: Path,
) -> None:
    """Test that the whitelist hides the flattening of a real round trip and nothing else.

    `gpa-flattening` is the one whitelist entry the fbc round trip relies on,
    and `R_PFL` and `R_ATPS4r` of `FBC_ECOLI_CORE_SBML` are the only two
    associations of that fixture it applies to, see
    `test_gpa_flattening_pins_every_association_libsbml_changes`. Both forms
    are spelled out here, so a round trip which changes an association in any
    other way fails this even where the entry would accept it; the entry
    itself is held to the two strings as well.

    The entry hides that flattening and nothing more, which the synthetic
    change at the end shows: one gene of the association written back is
    replaced, and the comparison reports exactly that reaction.
    """
    doc_in, doc_out = roundtrip_document(FBC_ECOLI_CORE_SBML, tmp_path)
    pinned = {f"model/reaction:{reaction_id}" for reaction_id in FLATTENED}
    for reaction_id, flattened in FLATTENED.items():
        assert _association(doc_in, reaction_id) == NESTED[reaction_id]
        assert _association(doc_out, reaction_id) == flattened
        assert flattened != NESTED[reaction_id]
        assert _normalization("gpa-flattening").equivalent(
            NESTED[reaction_id], flattened
        )

    differences = structural_diff(doc_in, doc_out)

    assert [str(d) for d in differences if d.element_id in pinned] == []

    _set_association(doc_out, "R_PFL", FLATTENED["R_PFL"].replace("G_b3114", "G_b3115"))

    changed = structural_diff(doc_in, doc_out)

    assert [(d.construct, d.element_id, d.attribute) for d in changed] == [
        ("fbc.geneProductAssociation", "model/reaction:R_PFL", "association")
    ]


@pytest.mark.parametrize(
    "before, after, equivalent",
    [
        ("((a and b) and c)", "(a and b and c)", True),
        ("(a and (b and c))", "(a and b and c)", True),
        ("((a or b) or (c or d))", "(a or b or c or d)", True),
        ("(a and b)", "(a and b)", True),
        # another operator, order, operand, repetition or grouping
        ("((a and b) and c)", "(a or b or c)", False),
        ("((a and b) or c)", "(a and b or c)", False),
        ("((a and b) and c)", "(a and c and b)", False),
        ("((a and b) and c)", "(a and b and d)", False),
        ("((a and b) and c)", "(a and b)", False),
        ("((a and b) and c)", "(a and b and c and c)", False),
        ("((a or b) and c)", "(a or b and c)", False),
        # the reverse, and a regrouping, which libsbml never writes
        ("(a and b and c)", "((a and b) and c)", False),
        ("(a and (b and c))", "((a and b) and c)", False),
        ("(a)", "a", False),
        ("(a and b", "(a and b)", False),
    ],
)
def test_gpa_flattening_is_narrow(before: str, after: str, equivalent: bool) -> None:
    """Test that the GPA flattening accepts only same-operator flattening."""
    assert _normalization("gpa-flattening").equivalent(before, after) is equivalent


def _l3_roundtrip_math(mathml: str) -> tuple[str, str]:
    """Write MathML, and write it again after a round trip as an L3 formula.

    Args:
        mathml: the content of a `math` element

    Returns:
        the MathML before and after the round trip, as libsbml writes it
    """
    doc = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    ast: libsbml.ASTNode = libsbml.readMathMLFromString(
        '<math xmlns="http://www.w3.org/1998/Math/MathML" '
        'xmlns:sbml="http://www.sbml.org/sbml/level3/version2/core">'
        f"{mathml}</math>"
    )
    formula: str = libsbml.formulaToL3String(ast)
    ast_again: libsbml.ASTNode = libsbml.parseL3FormulaWithModel(formula, model)
    return libsbml.writeMathMLToString(ast), libsbml.writeMathMLToString(ast_again)


@pytest.mark.parametrize(
    "mathml, equivalent",
    [
        ("<cn> 1 </cn>", True),
        ("<cn> 1.0 </cn>", True),
        ('<cn sbml:units="mole"> 3 </cn>', True),
        ("<apply><times/><cn> 2 </cn><ci> x </ci></apply>", True),
        ('<cn type="integer"> 4 </cn>', True),
        ("<cn> 2.5 </cn>", True),
        # a negative real is read back as the unary minus of an integer
        ("<cn> -2 </cn>", False),
    ],
)
def test_cn_integer_is_what_the_l3_formula_does(mathml: str, equivalent: bool) -> None:
    """Test the `cn` normalization against the L3 formula round trip of libsbml."""
    before, after = _l3_roundtrip_math(mathml)

    assert _normalization("cn-integer").equivalent(before, after) is equivalent


def _math(content: str) -> str:
    """Write the content of a `math` element as libsbml writes math."""
    ast: libsbml.ASTNode = libsbml.readMathMLFromString(
        '<math xmlns="http://www.w3.org/1998/Math/MathML" '
        'xmlns:sbml="http://www.sbml.org/sbml/level3/version2/core">'
        f"{content}</math>"
    )
    mathml: str = libsbml.writeMathMLToString(ast)
    return mathml


@pytest.mark.parametrize(
    "before, after",
    [
        # another value, a real value, another unit, the other direction
        ("<cn> 1 </cn>", '<cn type="integer"> 2 </cn>'),
        ("<cn> 2.5 </cn>", '<cn type="integer"> 2 </cn>'),
        (
            '<cn sbml:units="mole"> 1 </cn>',
            '<cn sbml:units="litre" type="integer"> 1 </cn>',
        ),
        ('<cn type="integer"> 1 </cn>', "<cn> 1 </cn>"),
        ('<cn type="e-notation"> 1 <sep/> 3 </cn>', '<cn type="integer"> 1000 </cn>'),
        # the normalization together with another change
        (
            "<apply><plus/><cn> 1 </cn><ci> x </ci></apply>",
            '<apply><plus/><cn type="integer"> 1 </cn><ci> y </ci></apply>',
        ),
    ],
)
def test_cn_integer_is_narrow(before: str, after: str) -> None:
    """Test that the `cn` normalization accepts a real gaining `type="integer"` only."""
    assert not _normalization("cn-integer").equivalent(_math(before), _math(after))


#: MIRIAM URNs, as the corpus and the examples of pymetadata spell them
_URNS: list[str] = [
    "urn:miriam:chebi:CHEBI%3A33699",
    "urn:miriam:uniprot:P03023",
    "urn:miriam:obo.go:GO%3A0005623",
    "urn:miriam:biomodels.sbo:SBO%3A0000247",
    "urn:miriam:kegg.compound:C00031",
    "urn:miriam:taxonomy:9606",
    "urn:miriam:pubmed:10643997",
    "urn:miriam:ec-code:1.1.1.1",
    "urn:miriam:reactome:REACT_1234",
]

#: classic identifiers.org URLs, as the corpus spells them; pymetadata
#: canonicalizes them exactly as it canonicalizes a URN, see ruling C1a
_CLASSIC_URLS: list[str] = [
    "http://identifiers.org/chebi/CHEBI:12965",
    "http://identifiers.org/uniprot/P03023",
    "http://identifiers.org/go/GO:0005623",
    "http://identifiers.org/obo.go/GO:0005623",
    "http://identifiers.org/biomodels.sbo/SBO:0000247",
    "http://identifiers.org/kegg.compound/C00031",
    "http://identifiers.org/pubmed/10643997",
    "http://identifiers.org/bigg.metabolite/glc__D",
    "http://identifiers.org/asap/ABE-0000027",
    # the https flavour of the classic form
    "https://identifiers.org/taxonomy/9606",
]

#: the `http` spelling of the compact URL, as the corpus spells it; pymetadata
#: writes it as the `https` one, see ruling C1c
_COMPACT_URLS: list[str] = [
    "http://identifiers.org/BTO:0000131",
    "http://identifiers.org/SBO:0000625",
    "http://identifiers.org/FMA:12274",
    "http://identifiers.org/CHEBI:33699",
    "http://identifiers.org/GO:0005623",
    # a collection whose namespace is not embedded in its term
    "http://identifiers.org/uniprot:P03023",
    "http://identifiers.org/kegg.compound:C00031",
]

#: bare compact identifiers, as the corpus spells them; pymetadata writes the
#: compact URL of them, see ruling C1c
_BARE_IDENTIFIERS: list[str] = [
    "UO:0000021",
    "CHEBI:33699",
    "GO:0005623",
    "SBO:0000247",
    "uniprot:P03023",
]


@pytest.mark.parametrize(
    "resource", [*_URNS, *_CLASSIC_URLS, *_COMPACT_URLS, *_BARE_IDENTIFIERS]
)
def test_identifiers_org_is_what_pymetadata_does(resource: str) -> None:
    """Test the normalization against the canonicalization of pymetadata.

    `create_model` writes a resource as pymetadata normalizes it whenever the normalization keeps the collection and the term of the resource, and as given when it does not, see `_resource_for_cvterm` of `sbmlutils.metadata.annotator`. Whenever it does normalize, it writes exactly what pymetadata writes, so the whitelist entry has to accept that for each of the four source forms of ruling R5: a MIRIAM URN, a classic identifiers.org URL, the `http` spelling of the compact URL and a bare compact identifier. The expectation is measured, never spelled out here. This is about the whitelist entry, not about which resources are written that way, which is `tests/metadata/test_annotator.py`.
    """
    url = RDFAnnotation(BQB.IS, resource, validate=False).resource_normalized
    before = (("bqbiol:is", resource),)

    assert url is not None and url.startswith("https://identifiers.org/")
    assert _normalization("identifiers-org").equivalent(before, (("bqbiol:is", url),))


@pytest.mark.parametrize(
    "before, after",
    [
        # a URN, with and without the collection as the prefix of its term
        (
            ("bqbiol:is", "urn:miriam:chebi:CHEBI%3A33699"),
            ("bqbiol:is", "https://identifiers.org/CHEBI:33699"),
        ),
        (
            ("bqbiol:is", "urn:miriam:uniprot:P03023"),
            ("bqbiol:is", "https://identifiers.org/uniprot:P03023"),
        ),
        # a classic identifiers.org URL, ruling C1a
        (
            ("bqbiol:is", "http://identifiers.org/chebi/CHEBI:12965"),
            ("bqbiol:is", "https://identifiers.org/CHEBI:12965"),
        ),
        (
            ("bqbiol:is", "http://identifiers.org/uniprot/P03023"),
            ("bqbiol:is", "https://identifiers.org/uniprot:P03023"),
        ),
        (
            ("bqbiol:is", "https://identifiers.org/taxonomy/9606"),
            ("bqbiol:is", "https://identifiers.org/taxonomy:9606"),
        ),
        # the two legacy collections pymetadata renames
        (
            ("bqbiol:is", "http://identifiers.org/obo.go/GO:0005623"),
            ("bqbiol:is", "https://identifiers.org/GO:0005623"),
        ),
        (
            ("bqbiol:is", "http://identifiers.org/biomodels.sbo/SBO:0000247"),
            ("bqbiol:is", "https://identifiers.org/SBO:0000247"),
        ),
        # the http spelling of the compact URL, ruling C1c
        (
            ("bqbiol:is", "http://identifiers.org/BTO:0000131"),
            ("bqbiol:is", "https://identifiers.org/BTO:0000131"),
        ),
        (
            ("bqbiol:is", "http://identifiers.org/uniprot:P03023"),
            ("bqbiol:is", "https://identifiers.org/uniprot:P03023"),
        ),
        # the bare compact identifier, ruling C1c
        (
            ("bqbiol:is", "UO:0000021"),
            ("bqbiol:is", "https://identifiers.org/UO:0000021"),
        ),
        (
            ("bqbiol:is", "uniprot:P03023"),
            ("bqbiol:is", "https://identifiers.org/uniprot:P03023"),
        ),
    ],
)
def test_identifiers_org_accepts_every_source_form(
    before: tuple[str, str], after: tuple[str, str]
) -> None:
    """Test that each of the four source forms of R5 is accepted as the compact URL."""
    assert _normalization("identifiers-org").equivalent((before,), (after,))


@pytest.mark.parametrize(
    "before, after",
    [
        # another qualifier, another term, another collection
        (
            ("bqbiol:is", "urn:miriam:chebi:CHEBI%3A33699"),
            ("bqbiol:isVersionOf", "https://identifiers.org/CHEBI:33699"),
        ),
        (
            ("bqbiol:is", "urn:miriam:uniprot:P03023"),
            ("bqbiol:is", "https://identifiers.org/uniprot:P03024"),
        ),
        (
            ("bqbiol:is", "urn:miriam:uniprot:P03023"),
            ("bqbiol:is", "https://identifiers.org/P03023"),
        ),
        (
            ("bqbiol:is", "urn:miriam:kegg.compound:C00031"),
            ("bqbiol:is", "https://identifiers.org/kegg.drug:C00031"),
        ),
        (
            ("bqbiol:is", "http://identifiers.org/uniprot/P03023"),
            ("bqbiol:is", "https://identifiers.org/uniprot:P03024"),
        ),
        (
            ("bqbiol:is", "http://identifiers.org/kegg.compound/C00031"),
            ("bqbiol:is", "https://identifiers.org/kegg.drug:C00031"),
        ),
        # the bare term pymetadata writes for a collection it does not know is a
        # loss of the collection, not a normalization, see rulings C1b and C1d
        (("bqbiol:is", "urn:miriam:foo:bar"), ("bqbiol:is", "bar")),
        (("bqbiol:is", "http://identifiers.org/foo/bar"), ("bqbiol:is", "bar")),
        (("bqbiol:is", "http://identifiers.org/sabiork/1406"), ("bqbiol:is", "1406")),
        # a bare term which carries its own prefix reads like a URI, and is a
        # loss of the collection all the same
        (("bqbiol:is", "urn:miriam:foo:BAR%3A123"), ("bqbiol:is", "BAR:123")),
        (
            ("bqbiol:is", "http://identifiers.org/foo/BAR:123"),
            ("bqbiol:is", "BAR:123"),
        ),
        (
            ("bqbiol:is", "http://identifiers.org/unit/UO:0000040"),
            ("bqbiol:is", "UO:0000040"),
        ),
        # a compact URL pymetadata reduces to its bare term, the same loss from a
        # resource which was canonical already
        (
            ("bqbiol:is", "https://identifiers.org/CMO:0000012"),
            ("bqbiol:is", "CMO:0000012"),
        ),
        # pymetadata drops the collection of a term which does not carry it, for
        # a collection whose namespace the registry says is embedded in the term
        (
            ("bqbiol:is", "http://identifiers.org/slm/000000035"),
            ("bqbiol:is", "https://identifiers.org/000000035"),
        ),
        # pymetadata shortens a term which repeats its collection, which changes
        # the term, see ruling C1d
        (
            ("bqbiol:is", "http://identifiers.org/reactome/REACTOME:R-HSA-70355.1"),
            ("bqbiol:is", "https://identifiers.org/reactome:R-HSA-70355.1"),
        ),
        # a bare compact identifier is a source, but only as itself: another
        # term, another prefix
        (
            ("bqbiol:is", "UO:0000021"),
            ("bqbiol:is", "https://identifiers.org/UO:0000022"),
        ),
        (
            ("bqbiol:is", "UO:0000021"),
            ("bqbiol:is", "https://identifiers.org/uo:0000021"),
        ),
        # a collection and term without a colon, and an arbitrary URL, are no
        # compact identifier
        (("bqbiol:is", "foo/bar"), ("bqbiol:is", "https://identifiers.org/foo/bar")),
        (
            ("bqbiol:is", "https://doi.org/10.1101/2021.06.15.448411"),
            ("bqbiol:is", "https://identifiers.org/10.1101/2021.06.15.448411"),
        ),
        # http instead of https
        (
            ("bqbiol:is", "urn:miriam:uniprot:P03023"),
            ("bqbiol:is", "http://identifiers.org/uniprot:P03023"),
        ),
        (
            ("bqbiol:is", "http://identifiers.org/uniprot/P03023"),
            ("bqbiol:is", "http://identifiers.org/uniprot:P03023"),
        ),
    ],
)
def test_identifiers_org_is_narrow(
    before: tuple[str, str], after: tuple[str, str]
) -> None:
    """Test that the normalization accepts nothing but the compact URL of its source."""
    assert not _normalization("identifiers-org").equivalent((before,), (after,))


def test_identifiers_org_needs_every_resource_matched() -> None:
    """Test that a resource lost next to a normalized one is not accepted."""
    before = (
        ("bqbiol:is", "urn:miriam:uniprot:P03023"),
        ("bqbiol:is", "http://identifiers.org/uniprot/P03024"),
    )
    after = (("bqbiol:is", "https://identifiers.org/uniprot:P03023"),)

    assert not _normalization("identifiers-org").equivalent(before, after)
    assert not _normalization("identifiers-org").equivalent(after, before)


def _set_association(doc: libsbml.SBMLDocument, reaction_id: str, infix: str) -> None:
    """Set the association of a reaction by gene product ids."""
    reaction: libsbml.Reaction = doc.getModel().getReaction(reaction_id)
    plugin: libsbml.FbcReactionPlugin = reaction.getPlugin("fbc")
    gpa: libsbml.GeneProductAssociation = plugin.getGeneProductAssociation()
    assert gpa.setAssociation(infix, True, False) == libsbml.LIBSBML_OPERATION_SUCCESS


def test_structural_diff_applies_the_whitelist() -> None:
    """Test that a whitelisted normalization is no difference, and nothing more is hidden.

    The damaged copy carries each of the three normalizations, which are not reported, and one change next to each, which is.
    """
    doc_in = _read(FBC_ECOLI_CORE_SBML)
    doc_out = _read(FBC_ECOLI_CORE_SBML)
    _set_association(doc_out, "R_PFL", FLATTENED["R_PFL"])
    gene_product: libsbml.GeneProduct = _fbc(doc_in).getGeneProduct("G_b1241")
    # both sources of the identifiers-org entry, a URN and a classic URL
    for doc, resources in [
        (
            doc_in,
            ["urn:miriam:uniprot:P0A9Q7", "http://identifiers.org/chebi/CHEBI:12965"],
        ),
        (
            doc_out,
            [
                "https://identifiers.org/uniprot:P0A9Q7",
                "https://identifiers.org/CHEBI:12965",
            ],
        ),
    ]:
        target: libsbml.GeneProduct = _fbc(doc).getGeneProduct("G_b1241")
        for qualifier, resource in zip(
            [libsbml.BQB_IS_ENCODED_BY, libsbml.BQB_IS_DESCRIBED_BY],
            resources,
            strict=True,
        ):
            term = libsbml.CVTerm(libsbml.BIOLOGICAL_QUALIFIER)
            term.setBiologicalQualifierType(qualifier)
            term.addResource(resource)
            assert target.addCVTerm(term) == libsbml.LIBSBML_OPERATION_SUCCESS
    assert gene_product.getNumCVTerms() == 3

    assert structural_diff(doc_in, doc_out) == []

    _set_association(doc_out, "R_PFL", FLATTENED["R_PFL"].replace("G_b3114", "G_b3115"))
    changed = structural_diff(doc_in, doc_out)
    assert [(d.construct, d.element_id, d.attribute) for d in changed] == [
        ("fbc.geneProductAssociation", "model/reaction:R_PFL", "association")
    ]


def test_structural_diff_applies_the_cn_whitelist_to_distrib_math() -> None:
    """Test that the `cn` normalization is applied to math, and nothing more is hidden."""
    doc_in = _read(UNCERTAINTY_SBML)
    doc_out = _read(UNCERTAINTY_SBML)
    parameter: libsbml.UncertParameter = (
        _uncertainties(doc_out).get(3).getUncertParameter(0)
    )
    formula: str = libsbml.formulaToL3String(parameter.getMath())
    assert parameter.setMath(
        libsbml.parseL3FormulaWithModel(formula, doc_out.getModel())
    ) == (libsbml.LIBSBML_OPERATION_SUCCESS)
    assert 'type="integer"' in libsbml.writeMathMLToString(parameter.getMath())

    assert structural_diff(doc_in, doc_out) == []

    formula = formula.replace("3 mole", "4 mole")
    assert parameter.setMath(
        libsbml.parseL3FormulaWithModel(formula, doc_out.getModel())
    ) == (libsbml.LIBSBML_OPERATION_SUCCESS)
    changed = structural_diff(doc_in, doc_out)
    assert [(d.construct, d.attribute) for d in changed] == [
        ("distrib.uncertParameter", "math")
    ]


# ---------------------------------------------------------------------------
# the report script, which sweeps the corpus with the comparison
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "content, expected, reported",
    [
        # what a worker killed while it writes its result leaves behind
        ('{"stage": "round trip", "pres', {}, True),
        ("", {}, True),
        ('["stage"]', {}, True),
        ('{"stage": "done"}', {"stage": "done"}, False),
        # a worker killed before it wrote anything
        (None, {}, False),
    ],
    ids=["truncated", "empty", "no object", "complete", "missing"],
)
def test_package_report_survives_an_unreadable_result(
    content: str | None, expected: dict[str, object], reported: bool, tmp_path: Path
) -> None:
    """Test that a result file a killed worker left behind ends its case, not the sweep.

    `scripts/package_report.py` runs every case in a process of its own so that a crash or a timeout ends one case. A worker killed while it writes its result leaves a truncated file, and reading it unguarded would raise through `executor.map` and end the whole sweep, which is the failure that isolation exists to prevent. The case is reported as a failed one instead.
    """
    from scripts.package_report import read_result

    result_path = tmp_path / "result.json"
    if content is not None:
        result_path.write_text(content)

    recorded, unreadable = read_result(result_path)

    assert recorded == expected
    assert bool(unreadable) is reported


def test_difference_names_its_package() -> None:
    """Test that a difference names the package of its construct."""
    difference = Difference("comp.modelDefinition.species", "x", "name", "a", "b")

    assert difference.package == "comp"
    assert "comp.modelDefinition.species" in str(difference)


# ---------------------------------------------------------------------------
# the distrib round trip
# ---------------------------------------------------------------------------
#: every distrib fixture of the repository, with the constructs it has to
#: contain; the list is every file of `resources/distrib` and
#: `resources/examples` which libsbml reads an uncertainty or a distrib
#: csymbol from
DISTRIB_FIXTURES: list[tuple[Path, tuple[str, ...]]] = [
    # six uncertainties on one parameter, between them every uncert parameter
    # and span type, a definitionURL, math and a nested listOfUncertParameters
    (
        UNCERTAINTY_SBML,
        ("distrib.package", "distrib.uncertainty", "distrib.uncertParameter"),
    ),
    # an uncertainty on an fbc gene product
    (
        ECOLI_EXPRESSION_SBML,
        ("distrib.package", "distrib.uncertainty", "distrib.uncertParameter"),
    ),
    # an uncertainty written from a model definition, with a span, two
    # parameters and the distribution of a `formula`
    (
        DISTRIB_UNCERTAINTIES_SBML,
        ("distrib.package", "distrib.uncertainty", "distrib.uncertParameter"),
    ),
    (
        DISTRIB_COMP_FLAT_SBML,
        ("distrib.package", "distrib.uncertainty", "distrib.uncertParameter"),
    ),
    # an uncertainty on a compartment of a model which also uses fbc
    (
        MODEL_SBML,
        ("distrib.package", "distrib.uncertainty", "distrib.uncertParameter"),
    ),
    # the distributions of distrib in the math of core elements
    (DISTRIB_ALL_SBML, ("distrib.package", "distrib.csymbol")),
    (DISTRIB_NORMAL_SBML, ("distrib.package", "distrib.csymbol")),
    (DISTRIB_DISTRIBUTIONS_SBML, ("distrib.package", "distrib.csymbol")),
]


@pytest.mark.parametrize(
    "sbml_path, constructs",
    DISTRIB_FIXTURES,
    ids=[sbml_path.name for sbml_path, _ in DISTRIB_FIXTURES],
)
def test_roundtrip_preserves_the_whole_distrib_content(
    sbml_path: Path,
    constructs: tuple[str, ...],
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that a round trip of a distrib fixture changes no distrib content at all.

    Between them the fixtures carry every distrib construct: `UNCERTAINTY_SBML` has six uncertainties with every type of uncert parameter and span, a definitionURL, math and a nested `listOfUncertParameters`, `ECOLI_EXPRESSION_SBML` has one on a gene product, `MODEL_SBML` one on a compartment, and the three files of distributions use the csymbols of distrib in the math of core elements. Each is asserted to have the constructs first, so preserving them cannot mean that the fixture has none, and every difference is asserted, not only the ones of the named constructs, so a distrib construct the round trip *adds* fails it too.

    `DISTRIB_COMP_SBML` is missing from the list on purpose: it is the same model as `DISTRIB_COMP_FLAT_SBML` with a comp port, and it is asserted with both of its packages in `test_roundtrip_of_a_distrib_comp_model_keeps_both_packages`.
    """
    counts, differences = package_roundtrip(sbml_path)
    assert [c for c in constructs if not counts[c]] == [], (
        f"the fixture has none of these constructs, so preserving them says "
        f"nothing: {[c for c in constructs if not counts[c]]}"
    )

    assert [str(d) for d in differences if d.package == "distrib"] == []


def test_roundtrip_of_a_distrib_comp_model_keeps_both_packages(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the uncertainty and the port of one model both survive.

    `DISTRIB_COMP_SBML` carries its uncertainty on a parameter which is also
    the target of a comp port, so it is the one fixture where the two packages
    meet. Both round trip, and every difference of the fixture is asserted, not
    only those of one package.
    """
    counts, differences = package_roundtrip(DISTRIB_COMP_SBML)
    assert counts["distrib.uncertainty"] == 1
    assert counts["distrib.uncertParameter"] == 4
    assert counts["comp.port"] == 1

    assert [str(d) for d in differences] == []


def _span_first_sbml(tmp_path: Path) -> Path:
    """Write a document whose uncertainty lists a span before a parameter.

    No fixture of the repository lists the children of an uncertainty in every
    order, and the order is what carries the meaning of the list, so this one
    is built with libsbml alone: a span, a parameter and a second span, on a
    parameter of the model.

    Args:
        tmp_path: the directory the file is written to

    Returns:
        the path of the written SBML file
    """
    ns: libsbml.SBMLNamespaces = libsbml.SBMLNamespaces(3, 2)
    ns.addPackageNamespace("distrib", 1)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(ns)
    doc.setPackageRequired("distrib", True)
    model: libsbml.Model = doc.createModel()
    model.setId("span_before_parameter")
    parameter: libsbml.Parameter = model.createParameter()
    parameter.setId("p1")
    parameter.setValue(5.0)
    parameter.setConstant(True)
    plugin: libsbml.DistribSBasePlugin = parameter.getPlugin("distrib")
    uncertainty: libsbml.Uncertainty = plugin.createUncertainty()

    span: libsbml.UncertSpan = uncertainty.createUncertSpan()
    span.setType(libsbml.DISTRIB_UNCERTTYPE_RANGE)
    span.setValueLower(2.0)
    span.setValueUpper(8.0)
    mean: libsbml.UncertParameter = uncertainty.createUncertParameter()
    mean.setType(libsbml.DISTRIB_UNCERTTYPE_MEAN)
    mean.setValue(5.0)
    interval: libsbml.UncertSpan = uncertainty.createUncertSpan()
    interval.setType(libsbml.DISTRIB_UNCERTTYPE_CONFIDENCEINTERVAL)
    interval.setValueLower(4.0)
    interval.setValueUpper(6.0)

    sbml_path = tmp_path / "span_before_parameter.xml"
    assert libsbml.writeSBMLToFile(doc, str(sbml_path))
    return sbml_path


def _child_elements(doc: libsbml.SBMLDocument) -> list[str]:
    """Name the children of the first uncertainty of the parameter `p1`.

    Args:
        doc: a document written by `_span_first_sbml`, which the caller holds

    Returns:
        `uncertParameter` or `uncertSpan` for every child, in document order
    """
    uncertainty: libsbml.Uncertainty = (
        doc.getModel().getParameter("p1").getPlugin("distrib").getUncertainty(0)
    )
    return [
        uncertainty.getUncertParameter(k).getElementName()
        for k in range(uncertainty.getNumUncertParameters())
    ]


def test_roundtrip_keeps_a_span_before_a_parameter(tmp_path: Path) -> None:
    """Test that the order of the children of an uncertainty survives.

    SBML holds the parameters and the spans of an uncertainty in one list, in
    which the position of an element is its only identity: distrib gives
    neither an id nor a reference to match them by, which is why
    `tests/structural.py` compares them in document order. The writer wrote
    every span before every parameter, so an uncertainty which lists them the
    other way round came back reordered.
    """
    sbml_path = _span_first_sbml(tmp_path)
    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
    assert _child_elements(doc_in) == ["uncertSpan", "uncertParameter", "uncertSpan"]

    assert _child_elements(doc_out) == ["uncertSpan", "uncertParameter", "uncertSpan"]
    assert [str(d) for d in structural_diff(doc_in, doc_out)] == []


def test_roundtrip_keeps_the_notes_of_an_uncertainty(tmp_path: Path) -> None:
    """Test that the notes of an uncertainty and of its children survive.

    The factory renders notes through markdown, and a round trip of notes
    which are already xhtml has to leave them as they are; no uncertainty of
    the repository carries notes, so the case is built here. Notes are
    compared as libsbml serializes them, see the docstring of
    `tests/structural.py`, and nothing about them is whitelisted.
    """
    sbml_path = _span_first_sbml(tmp_path)
    doc: libsbml.SBMLDocument = _read(sbml_path)
    uncertainty: libsbml.Uncertainty = (
        doc.getModel().getParameter("p1").getPlugin("distrib").getUncertainty(0)
    )
    note = '<body xmlns="http://www.w3.org/1999/xhtml"><p>%s</p></body>'
    assert uncertainty.setNotes(note % "measured in 2021") == 0
    assert uncertainty.getUncertParameter(0).setNotes(note % "min and max") == 0
    assert uncertainty.getUncertParameter(1).setNotes(note % "of three runs") == 0
    sbml_path = tmp_path / "notes_on_an_uncertainty.xml"
    assert libsbml.writeSBMLToFile(doc, str(sbml_path))

    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)

    assert [str(d) for d in structural_diff(doc_in, doc_out)] == []
    written: libsbml.Uncertainty = (
        doc_out.getModel().getParameter("p1").getPlugin("distrib").getUncertainty(0)
    )
    assert "measured in 2021" in written.getNotesString()
    assert "min and max" in written.getUncertParameter(0).getNotesString()


def _typeless_sbml(tmp_path: Path) -> Path:
    """Write a document whose uncert parameter and span state no type.

    SBML requires a `distrib:type`, so no fixture of the repository leaves it
    out and this document is built with libsbml alone; libsbml writes it,
    reads it back and reports the missing attribute as an error of the
    document, on both sides of the round trip.

    Args:
        tmp_path: the directory the file is written to

    Returns:
        the path of the written SBML file
    """
    ns: libsbml.SBMLNamespaces = libsbml.SBMLNamespaces(3, 2)
    ns.addPackageNamespace("distrib", 1)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(ns)
    doc.setPackageRequired("distrib", True)
    model: libsbml.Model = doc.createModel()
    model.setId("uncert_parameter_without_a_type")
    parameter: libsbml.Parameter = model.createParameter()
    parameter.setId("p1")
    parameter.setValue(5.0)
    parameter.setConstant(True)
    uncertainty: libsbml.Uncertainty = parameter.getPlugin(
        "distrib"
    ).createUncertainty()
    typeless: libsbml.UncertParameter = uncertainty.createUncertParameter()
    typeless.setValue(3.0)
    span: libsbml.UncertSpan = uncertainty.createUncertSpan()
    span.setValueLower(1.0)
    span.setValueUpper(5.0)

    sbml_path = tmp_path / "uncert_parameter_without_a_type.xml"
    assert libsbml.writeSBMLToFile(doc, str(sbml_path))
    return sbml_path


def test_roundtrip_keeps_an_uncert_parameter_without_a_type(tmp_path: Path) -> None:
    """Test that an element which states no type round trips as it is.

    `distrib:type` is required on an uncert parameter and libsbml reads an
    element without it all the same. Such an element is as much of the
    document as any other: a round trip which drops it, or which invents a
    type for it, changes the document, and the comparison sees both.
    """
    sbml_path = _typeless_sbml(tmp_path)
    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
    uncertainty: libsbml.Uncertainty = (
        doc_in.getModel().getParameter("p1").getPlugin("distrib").getUncertainty(0)
    )
    assert not uncertainty.getUncertParameter(0).isSetType()

    assert [str(d) for d in structural_diff(doc_in, doc_out)] == []
    written: libsbml.Uncertainty = (
        doc_out.getModel().getParameter("p1").getPlugin("distrib").getUncertainty(0)
    )
    assert written.getNumUncertParameters() == 2
    assert not written.getUncertParameter(0).isSetType()


# ---------------------------------------------------------------------------
# the comp round trip
# ---------------------------------------------------------------------------
def _comp_differences(differences: list[Difference]) -> list[str]:
    """Get the comp differences of a round trip, as lines.

    Every construct of comp is prefixed `comp.`, the core elements of a model definition included (`comp.modelDefinition.species`), so the package of the construct is the whole filter, see `Difference.package`.

    Args:
        differences: the differences of a round trip, of every package

    Returns:
        one line per comp difference, in the order of the differences
    """
    return [str(d) for d in differences if d.package == "comp"]


def test_roundtrip_preserves_the_submodels_of_icg_body(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the submodel of `COMP_ICG_BODY` survives a round trip.

    The model is a whole-body PBPK model whose liver is a submodel of an external model definition, so it has exactly one `<comp:submodel>`, with an id and a name.
    """
    comparison = package_roundtrip(COMP_ICG_BODY)
    assert comparison[0]["comp.submodel"] == 1

    _assert_preserved(comparison, "comp.submodel")


@requires_testsuite
def test_roundtrip_preserves_the_deletions_of_a_submodel(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the deletions of a submodel survive a round trip.

    SBML puts a `<comp:deletion>` under the submodel it deletes from; `Model.deletions` holds it with the id of that submodel instead, which is what `Deletion.create_sbml` resolves it against. Case 01157 deletes by `metaIdRef`, case 01166 by `idRef` and its deletion carries an id of its own.
    """
    for case in ("01157", "01166"):
        comparison = package_roundtrip(testsuite_case(case))
        assert comparison[0]["comp.deletion"], f"case {case} has no deletion"
        _assert_preserved(comparison, "comp.deletion", "comp.submodel")


def test_roundtrip_preserves_the_ports_of_icg_body(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the 16 ports of `COMP_ICG_BODY` survive a round trip.

    Every port has an id, a name, a metaid and an sboTerm of its own, and each references a parameter or a species of the model by `idRef`.
    """
    comparison = package_roundtrip(COMP_ICG_BODY)
    assert comparison[0]["comp.port"] == 16

    _assert_preserved(comparison, "comp.port")


def test_roundtrip_writes_each_port_exactly_once(tmp_path: Path) -> None:
    """Test that a port read is written once, not once per way of writing it.

    `sbmlutils.factory` writes a port from the `ports` of the model and from the `port=True`/`port=Port(...)` shorthand of the element it references, and an element which carried both would be given two ports. The parser reads a port into the `ports` of the model only: the list keeps the port's own id, name, metaid, sboTerm and order, and it does not depend on the referenced element accepting a `port=` keyword, which many do not.
    """
    doc_in, doc_out = roundtrip_document(COMP_ICG_BODY, tmp_path)
    comp_in: libsbml.CompModelPlugin = doc_in.getModel().getPlugin("comp")
    assert comp_in.getNumPorts() == 16

    comp_out: libsbml.CompModelPlugin = doc_out.getModel().getPlugin("comp")

    assert comp_out.getNumPorts() == 16
    assert [comp_out.getPort(k).getId() for k in range(16)] == [
        comp_in.getPort(k).getId() for k in range(16)
    ]


#: cases of the SBML test suite whose replacements exercise a shape of their
#: own, with the constructs each of them has to preserve
REPLACEMENT_CASES: list[tuple[str, tuple[str, ...]]] = [
    # an sBaseRef chain of two levels under a replaced element
    ("01132", ("comp.replacedElement", "comp.sBaseRef")),
    # the same chain, and a replacedBy which continues into a submodel too
    ("01133", ("comp.replacedElement", "comp.replacedBy", "comp.sBaseRef")),
    ("01134", ("comp.replacedElement", "comp.replacedBy", "comp.sBaseRef")),
    # a replaced element with a conversion factor
    ("01137", ("comp.replacedElement", "comp.submodel")),
    # a replaced element which names a deletion of its submodel, and the only
    # deletion of the suite with an id of its own
    ("01166", ("comp.replacedElement", "comp.deletion")),
]


@requires_testsuite
@pytest.mark.parametrize(
    "case, constructs", REPLACEMENT_CASES, ids=[case for case, _ in REPLACEMENT_CASES]
)
def test_roundtrip_preserves_replacements_and_their_sbaseref_chain(
    case: str,
    constructs: tuple[str, ...],
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that a replaced element, a replacedBy and their nested chain survive.

    A `<comp:replacedElement>` and a `<comp:replacedBy>` sit on the element they replace, and either can continue its reference into a submodel of the submodel it names, through a nested `<comp:sBaseRef>` of arbitrary depth. Each level is compared under the level above it, in order, see the docstring of `tests/structural.py`, so a chain which comes back one level short is a difference. Every comp difference of the case is asserted, not only those of the named constructs, so comp content the round trip *adds* fails it too.
    """
    counts, differences = package_roundtrip(testsuite_case(case))
    missing = [c for c in constructs if not counts[c]]
    assert missing == [], f"case {case} has none of {missing}"

    assert _comp_differences(differences) == []


@requires_testsuite
def test_roundtrip_preserves_a_replaced_element_of_an_element_without_an_id(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that a replacement of an element which has only a metaid survives.

    `sbmlutils.factory` holds a replaced element in the `replaced_elements` of the model, where it names the element it replaces in `elementRef`, which `ReplacedElement.create_sbml` resolves against the model it writes into. A rule, an initial assignment, an event assignment and a kinetic law have an id only from SBML L3V2 on, and cases 01150 and 01163 of the SBML test suite each put a `<comp:replacedElement>` on a rate rule which carries a metaid and no id, so `elementRef` names such an element by its metaid.
    """
    for case in ("01150", "01163"):
        comparison = package_roundtrip(testsuite_case(case))
        assert comparison[0]["comp.replacedElement"] == 2, case
        assert _comp_differences(comparison[1]) == [], case


def _rule_replacement_sbml(
    tmp_path: Path,
    name: str,
    rule_metaid: str | None = None,
    unit_id: str | None = None,
) -> Path:
    """Write a document whose replaced element sits on a rate rule.

    A rule of SBML L3V2 need carry neither an id nor a metaid, and comp puts a `<comp:replacedElement>` on any element, so the id `elementRef` names such an element by is its metaid, if it has one. No document of the repository has one at all, so these are built with libsbml alone.

    Args:
        tmp_path: the directory the file is written to
        name: the id of the model and the stem of the file
        rule_metaid: the metaid of the rate rule, `None` for a rule with no metaid and no id
        unit_id: the id of a unit definition to add to the model, `None` for a model without one

    Returns:
        the path of the written SBML file
    """
    ns: libsbml.SBMLNamespaces = libsbml.SBMLNamespaces(3, 2)
    ns.addPackageNamespace("comp", 1)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(ns)
    doc.setPackageRequired("comp", True)
    model: libsbml.Model = doc.createModel()
    model.setId(name)
    if unit_id is not None:
        udef: libsbml.UnitDefinition = model.createUnitDefinition()
        udef.setId(unit_id)
        unit: libsbml.Unit = udef.createUnit()
        unit.setKind(libsbml.UNIT_KIND_SECOND)
        unit.setExponent(1.0)
        unit.setScale(0)
        unit.setMultiplier(1.0)
    parameter: libsbml.Parameter = model.createParameter()
    parameter.setId("p1")
    parameter.setValue(1.0)
    parameter.setConstant(False)
    rule: libsbml.RateRule = model.createRateRule()
    rule.setVariable("p1")
    rule.setMath(libsbml.parseL3Formula("3"))
    if rule_metaid is not None:
        rule.setMetaId(rule_metaid)
    comp: libsbml.CompModelPlugin = model.getPlugin("comp")
    submodel: libsbml.Submodel = comp.createSubmodel()
    submodel.setId("sub1")
    submodel.setModelRef("md1")
    replaced: libsbml.ReplacedElement = rule.getPlugin("comp").createReplacedElement()
    replaced.setSubmodelRef("sub1")
    replaced.setIdRef("p10")
    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    definition: libsbml.ModelDefinition = doc_comp.createModelDefinition()
    definition.setId("md1")
    inner: libsbml.Parameter = definition.createParameter()
    inner.setId("p10")
    inner.setValue(10.0)
    inner.setConstant(False)

    sbml_path = tmp_path / f"{name}.xml"
    assert libsbml.writeSBMLToFile(doc, str(sbml_path))
    return sbml_path


#: the documents whose `<comp:replacedElement>` sits on a rate rule which
#: `elementRef` cannot name, with the metaid of that rule and the unit
#: definition the model has, and the part of the report which says why
UNNAMEABLE: list[tuple[str, str | None, str | None, str]] = [
    # no id and no metaid: nothing to name it by at all
    ("a_rule_without_a_name", None, None, "has neither"),
    # a metaid which is the id of a parameter: `ReplacedElement.create_sbml`
    # resolves an SId first, so this would attach the replacement to `p1`
    ("a_rule_whose_metaid_is_an_id", "p1", None, "is the id of"),
    # a metaid which is the id of a unit definition, which `create_sbml`
    # resolves next, before it tries a metaid
    ("a_rule_whose_metaid_is_a_unit", "u1", "u1", "is the id of"),
]


@pytest.mark.parametrize(
    "name, rule_metaid, unit_id, reason",
    UNNAMEABLE,
    ids=[name for name, _, _, _ in UNNAMEABLE],
)
def test_parser_reports_a_replaced_element_it_cannot_name(
    name: str,
    rule_metaid: str | None,
    unit_id: str | None,
    reason: str,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that a replacement whose element cannot be named is reported and dropped.

    `elementRef` names the element a replacement sits on, and `ReplacedElement.create_sbml` resolves it as the id of an element, then as the id of a unit definition, then as a metaid. An element which has neither an id nor a metaid cannot be named at all; an element whose metaid is the id of another element or of a unit definition would be named ambiguously, and the replacement would be written into that other element, silently and wrongly. Both are losses, and a loss which is not reported is a silent one: the parser names the kind of element it sat on and drops the replacement, as it does for an uncertainty which cannot be written back.
    """
    sbml_path = _rule_replacement_sbml(tmp_path, name, rule_metaid, unit_id)

    with caplog.at_level(logging.ERROR, logger="sbmlutils.parser"):
        model = sbml_to_model(sbml_path)

    lost = [
        record.getMessage()
        for record in caplog.records
        if "replacedElement" in record.getMessage()
    ]
    assert len(lost) == 1, caplog.records
    assert "rateRule" in lost[0]
    assert reason in lost[0]
    if rule_metaid is not None:
        assert rule_metaid in lost[0]
    assert model.replaced_elements == []


def test_parser_names_a_replaced_element_by_an_unambiguous_metaid(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a metaid which names nothing else is used and reported about.

    The counterpart of the three losses above, and the shape the two cases of the SBML test suite have: a rate rule whose metaid is the id of no element and of no unit definition names that rule unambiguously, so the replacement is kept and nothing is reported.
    """
    sbml_path = _rule_replacement_sbml(tmp_path, "a_rule_with_a_metaid", "rule_meta")

    with caplog.at_level(logging.ERROR, logger="sbmlutils.parser"):
        model = sbml_to_model(sbml_path)

    assert [record.getMessage() for record in caplog.records] == []
    assert [r.elementRef for r in model.replaced_elements] == ["rule_meta"]


def test_libsbml_has_no_list_of_replaced_elements_until_one_is_added(
    tmp_path: Path,
) -> None:
    """Test the libsbml behaviour the parser has to count around.

    libsbml 5.21.2 creates the `<comp:listOfReplacedElements>` of an element
    only when its first replaced element is added, and answers
    `getListOfReplacedElements()` with `None` until then, on a fresh document
    and on one read from a file alike. Iterating that getter is therefore a
    `TypeError` on every element which has no replacement, which is nearly
    every element of every document, so `_parse_replaced_elements` counts with
    `getNumReplacedElements()` instead. `tests/structural.py` handles the same
    thing in `_items`. This is pinned so that the count is not tidied back
    into an iteration.
    """
    sbml_path = _rule_replacement_sbml(tmp_path, "a_rule_with_a_metaid", "rule_meta")
    doc: libsbml.SBMLDocument = _read(sbml_path)
    model: libsbml.Model = doc.getModel()

    parameter_comp: libsbml.CompSBasePlugin = model.getParameter("p1").getPlugin("comp")
    assert parameter_comp.getNumReplacedElements() == 0
    assert parameter_comp.getListOfReplacedElements() is None

    rule_comp: libsbml.CompSBasePlugin = model.getRule("p1").getPlugin("comp")
    assert rule_comp.getNumReplacedElements() == 1
    assert rule_comp.getListOfReplacedElements() is not None


def _replaced_by_sbml(tmp_path: Path) -> Path:
    """Write a document with a `<comp:replacedBy>` on the elements which lose it.

    comp allows a `<comp:replacedBy>` on every SBML element, and libsbml writes and reads one back on a `<speciesReference>`, a `<localParameter>` and a `<kineticLaw>` as it does on a species, which is measured by reading the document this writes: all four carry one here. `EquationPart` has no `replacedBy` field and a `LocalParameter` does not offer one, so those two are the elements of this document whose replacement `_drop_replaced_by` drops; the species and the kinetic law are the controls which keep it. No document of the repository has one on such an element, so this one is built with libsbml alone.

    Args:
        tmp_path: the directory the file is written to

    Returns:
        the path of the written SBML file
    """
    ns: libsbml.SBMLNamespaces = libsbml.SBMLNamespaces(3, 2)
    ns.addPackageNamespace("comp", 1)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(ns)
    doc.setPackageRequired("comp", True)
    model: libsbml.Model = doc.createModel()
    model.setId("replaced_by_on_every_element")
    compartment: libsbml.Compartment = model.createCompartment()
    compartment.setId("c")
    compartment.setSize(1.0)
    compartment.setSpatialDimensions(3)
    compartment.setConstant(True)
    species: libsbml.Species = model.createSpecies()
    species.setId("S1")
    species.setCompartment("c")
    species.setInitialConcentration(1.0)
    species.setHasOnlySubstanceUnits(False)
    species.setBoundaryCondition(False)
    species.setConstant(False)
    reaction: libsbml.Reaction = model.createReaction()
    reaction.setId("R1")
    reaction.setReversible(False)
    reactant: libsbml.SpeciesReference = reaction.createReactant()
    reactant.setId("sr1")
    reactant.setSpecies("S1")
    reactant.setStoichiometry(1.0)
    reactant.setConstant(True)
    kinetic_law: libsbml.KineticLaw = reaction.createKineticLaw()
    kinetic_law.setMath(libsbml.parseL3Formula("k1 * S1"))
    local: libsbml.LocalParameter = kinetic_law.createLocalParameter()
    local.setId("k1")
    local.setValue(0.1)
    comp: libsbml.CompModelPlugin = model.getPlugin("comp")
    submodel: libsbml.Submodel = comp.createSubmodel()
    submodel.setId("sub1")
    submodel.setModelRef("md1")
    for element in (species, reactant, kinetic_law, local):
        replaced_by: libsbml.ReplacedBy = element.getPlugin("comp").createReplacedBy()
        replaced_by.setSubmodelRef("sub1")
        replaced_by.setIdRef("inner")
    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    definition: libsbml.ModelDefinition = doc_comp.createModelDefinition()
    definition.setId("md1")
    inner: libsbml.Parameter = definition.createParameter()
    inner.setId("inner")
    inner.setValue(10.0)
    inner.setConstant(True)

    sbml_path = tmp_path / "replaced_by_on_every_element.xml"
    assert libsbml.writeSBMLToFile(doc, str(sbml_path))
    return sbml_path


def test_parser_reports_a_replaced_by_it_cannot_write(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a replacedBy on an element which cannot carry one is reported.

    comp allows a `<comp:replacedBy>` on every element and the parser reads it from every element, but a species reference is an `EquationPart` with no field for it, and a `LocalParameter` does not offer one because no `<comp:replacedBy>` on a `<localParameter>` is valid, so those two would lose it in the writer without a word. `_drop_replaced_by` drops it where the element is known and names it instead. The species and the kinetic law of the same document keep their replacedBy, so the test says what is dropped and not merely that something is.
    """
    sbml_path = _replaced_by_sbml(tmp_path)
    doc: libsbml.SBMLDocument = _read(sbml_path)
    carried = [
        element.getElementName()
        for element in doc.getModel().getListOfAllElements()
        if isinstance(element.getPlugin("comp"), libsbml.CompSBasePlugin)
        and element.getPlugin("comp").isSetReplacedBy()
    ]
    assert sorted(carried) == [
        "kineticLaw",
        "localParameter",
        "species",
        "speciesReference",
    ]

    with caplog.at_level(logging.ERROR, logger="sbmlutils.parser"):
        model = sbml_to_model(sbml_path)

    dropped = [
        record.getMessage()
        for record in caplog.records
        if "replacedBy" in record.getMessage()
    ]
    assert len(dropped) == 2, caplog.records
    assert sorted(message.split("'")[0].split()[-1] for message in dropped) == [
        "localParameter",
        "speciesReference",
    ]
    # the species and the kinetic law of the same document keep theirs, and
    # neither of the two elements which lost theirs carries one into the writer
    assert model.species[0].replacedBy is not None
    reactant = model.reactions[0].equation.reactants[0]
    assert not hasattr(reactant, "replacedBy")
    kinetic_law = model.reactions[0].formula
    assert kinetic_law is not None
    assert kinetic_law.replacedBy is not None
    assert kinetic_law.local_parameters[0].replacedBy is None


#: the only fixture of the repository with a `<comp:modelDefinition>`
MODEL_DEFINITIONS_SBML: Path = EXAMPLES_DIR / "model_definitions.xml"


def test_roundtrip_preserves_a_model_definition(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that a `<comp:modelDefinition>` survives a round trip with its content.

    A model definition is a model of its own next to the model of the document; `sbmlutils.parser` reads it by constructing a `ModelDefinition` and recursing into the same `_parse_model_body` the model of the document goes through, so its core elements, its unit definitions and its package content come along. The comparison compares a model definition recursively, core content included, since nothing else sees it, see the docstring of `tests/structural.py`.
    """
    counts, differences = package_roundtrip(MODEL_DEFINITIONS_SBML)
    assert counts["comp.modelDefinition"] == 1
    assert counts["comp.modelDefinition.species"]
    assert counts["comp.modelDefinition.compartment"]

    assert _comp_differences(differences) == []


@requires_testsuite
def test_roundtrip_preserves_the_whole_content_of_a_model_definition(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that every kind of element of a model definition survives.

    Cases 01142 and 01169 of the SBML test suite are the two whose model definitions hold species, reactions, rules and events between them, which the comparison compares element by element with their L3V2 core attributes and their math.
    """
    for case in ("01142", "01169"):
        counts, differences = package_roundtrip(testsuite_case(case))
        for element in ("species", "reaction", "rateRule", "event", "trigger"):
            assert counts[f"comp.modelDefinition.{element}"], f"{case}: {element}"
        assert _comp_differences(differences) == [], case


def _comp_of_definitions(doc: libsbml.SBMLDocument) -> list[tuple[int, int]]:
    """Count the submodels and the ports inside each model definition of a document.

    The count is read from the comp plugin of the model definition itself, not from the comp content of the document, which is what separates a submodel of a `<comp:modelDefinition>` from one of the `<model>`.

    Args:
        doc: a document which declares comp, which the caller has to hold

    Returns:
        the number of submodels and the number of ports of every model definition, in document order
    """
    comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    counts: list[tuple[int, int]] = []
    for k in range(comp.getNumModelDefinitions()):
        definition_comp: libsbml.CompModelPlugin = comp.getModelDefinition(k).getPlugin(
            "comp"
        )
        counts.append(
            (definition_comp.getNumSubmodels(), definition_comp.getNumPorts())
        )
    return counts


@requires_testsuite
@pytest.mark.parametrize(
    "case, expected",
    [("01153", [(0, 1), (1, 1)]), ("01166", [(0, 7), (0, 4)])],
)
def test_roundtrip_preserves_the_submodels_and_ports_of_a_model_definition(
    case: str, expected: list[tuple[int, int]], tmp_path: Path
) -> None:
    """Test that the comp content of a model definition survives too.

    A model definition holds submodels and ports of its own, which the recursion into `_parse_model_body` reads with the same parser as those of the model of the document. Case 01153 nests a submodel in the second of its two model definitions and gives each of them a port, case 01166 gives its two model definitions seven and four ports. They are counted on the model definitions themselves, before and after, so that comp content of the *model* of the document cannot stand in for them, and the round trip is asserted to change no comp content at all besides.
    """
    doc_in, doc_out = roundtrip_document(testsuite_case(case), tmp_path)
    assert _comp_of_definitions(doc_in) == expected

    assert _comp_of_definitions(doc_out) == expected
    assert _comp_differences(structural_diff(doc_in, doc_out)) == []


#: five external model definitions, one per submodel
MINIMAL_MODEL_COMP_SBML: Path = EXAMPLES_DIR / "minimal_model_comp.xml"

#: the fixture whose submodels replace 30 unit definitions of the top model
DIAUXIC_TOP_SBML: Path = RESOURCES_DIR / "models" / "dfba" / "diauxic_top.xml"


def test_roundtrip_preserves_replaced_unit_definitions(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that a replaced element on a unit definition survives.

    A unit definition lives in a namespace of its own, so `model.getElementBySId` does not find it and `ReplacedElement.create_sbml` falls back to `model.getUnitDefinition`. `diauxic_top.xml` is the fixture which exercises that: 30 of its 61 replaced elements sit on a unit definition, the rest on a species, a compartment or a parameter.
    """
    counts, differences = package_roundtrip(DIAUXIC_TOP_SBML)
    assert counts["comp.replacedElement"] == 61
    assert counts["comp.externalModelDefinition"] == 3

    assert _comp_differences(differences) == []


def test_roundtrip_preserves_external_model_definitions(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that a `<comp:externalModelDefinition>` survives with its attributes.

    `COMP_ICG_BODY` names its liver model in a file of its own, `MINIMAL_MODEL_COMP_SBML` names five, and the comparison compares `source`, `modelRef` and `md5` of each, with its metadata.
    """
    for sbml_path, count in [(COMP_ICG_BODY, 1), (MINIMAL_MODEL_COMP_SBML, 5)]:
        comparison = package_roundtrip(sbml_path)
        assert comparison[0]["comp.externalModelDefinition"] == count
        _assert_preserved(comparison, "comp.externalModelDefinition")


def _external_sbml(tmp_path: Path, source: str) -> Path:
    """Write a document whose only comp content is one external model definition.

    Args:
        tmp_path: the directory the file is written to
        source: the `comp:source` of the external model definition

    Returns:
        the path of the written SBML file
    """
    ns: libsbml.SBMLNamespaces = libsbml.SBMLNamespaces(3, 2)
    ns.addPackageNamespace("comp", 1)
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(ns)
    doc.setPackageRequired("comp", True)
    model: libsbml.Model = doc.createModel()
    model.setId("references_an_external_model")
    parameter: libsbml.Parameter = model.createParameter()
    parameter.setId("p1")
    parameter.setValue(1.0)
    parameter.setConstant(True)
    comp: libsbml.CompModelPlugin = model.getPlugin("comp")
    submodel: libsbml.Submodel = comp.createSubmodel()
    submodel.setId("sub1")
    submodel.setModelRef("external")
    doc_comp: libsbml.CompSBMLDocumentPlugin = doc.getPlugin("comp")
    external: libsbml.ExternalModelDefinition = doc_comp.createExternalModelDefinition()
    external.setId("external")
    external.setSource(source)
    external.setModelRef("the_external_model")
    external.setMd5("d41d8cd98f00b204e9800998ecf8427e")

    sbml_path = tmp_path / "references_an_external_model.xml"
    assert libsbml.writeSBMLToFile(doc, str(sbml_path))
    return sbml_path


def _external_model_sbml(tmp_path: Path) -> Path:
    """Write the external model a document can point at, with a telltale id.

    Args:
        tmp_path: the directory the file is written to

    Returns:
        the path of the written SBML file
    """
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(3, 2)
    model: libsbml.Model = doc.createModel()
    model.setId("the_external_model")
    parameter: libsbml.Parameter = model.createParameter()
    parameter.setId("only_in_the_external_model")
    parameter.setValue(42.0)
    parameter.setConstant(True)

    sbml_path = tmp_path / "the_external_model.xml"
    assert libsbml.writeSBMLToFile(doc, str(sbml_path))
    return sbml_path


def test_roundtrip_does_not_inline_an_external_model_definition(
    tmp_path: Path,
) -> None:
    """Test that the content of a referenced model does not end up in the document.

    An external model definition names a model in another file, and the round trip preserves that reference rather than resolving it. The file here does exist and its model holds a parameter of a telltale id, so a round trip which read it and wrote its content into the document, in a `<comp:modelDefinition>` or inline, would be caught by the id turning up in the file written.

    That libsbml itself opens no file cannot be asserted from python: it reads and writes through `libsbml.readSBMLFromFile` and `libsbml.writeSBMLToFile`, whose file IO happens in C++ and passes no python file API, so a spy on `open` records nothing whatever libsbml does and could never fail. What the round trip writes is the observable half, and it is what this test and `test_roundtrip_keeps_an_external_model_definition_whose_source_is_missing` assert between them.
    """
    external_path = _external_model_sbml(tmp_path)
    sbml_path = _external_sbml(tmp_path, external_path.name)
    assert "only_in_the_external_model" in external_path.read_text()

    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)

    written = (tmp_path / f"{sbml_path.stem}-roundtrip.xml").read_text()
    assert "only_in_the_external_model" not in written
    comp: libsbml.CompSBMLDocumentPlugin = doc_out.getPlugin("comp")
    assert comp.getNumModelDefinitions() == 0
    assert structural_diff(doc_in, doc_out) == []


def test_roundtrip_keeps_an_external_model_definition_whose_source_is_missing(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a source which resolves to nothing round trips as it is.

    A reference is preserved as a reference, whether or not the file is there, so a document whose `comp:source` names a file which does not exist round trips unchanged: the three attributes come back as they were, the structural comparison of the two documents is empty, and neither the parser nor the writer reports anything at all, which is what a round trip that tried to follow the reference could not do. libsbml reads such a document without an error too; only its consistency check reports the unresolved reference, id 1090101, which `create_model` reports and does not act on.
    """
    sbml_path = _external_sbml(tmp_path, "does_not_exist.xml")

    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)

    assert [record.getMessage() for record in caplog.records] == []
    assert structural_diff(doc_in, doc_out) == []
    comp: libsbml.CompSBMLDocumentPlugin = doc_out.getPlugin("comp")
    external: libsbml.ExternalModelDefinition = comp.getExternalModelDefinition(0)
    assert external.getSource() == "does_not_exist.xml"
    assert external.getModelRef() == "the_external_model"
    assert external.getMd5() == "d41d8cd98f00b204e9800998ecf8427e"


def test_roundtrip_preserves_the_comp_content_of_icg_body(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the whole comp content of `COMP_ICG_BODY` survives a round trip.

    The model is a whole-body PBPK model whose liver is a submodel of an external model definition: one submodel, 16 ports, six replaced elements and one external model definition, which is every comp construct this fixture has. Each is asserted to be in the document first, so preserving them cannot mean that the fixture has none, and every comp difference is asserted, not only those of the named constructs, so comp content the round trip *adds* fails it too.
    """
    counts, differences = package_roundtrip(COMP_ICG_BODY)
    assert counts["comp.submodel"] == 1
    assert counts["comp.port"] == 16
    assert counts["comp.replacedElement"] == 6
    assert counts["comp.externalModelDefinition"] == 1

    assert _comp_differences(differences) == []


def test_roundtrip_of_a_flat_model_gains_no_comp_content(
    package_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that a model without comp does not gain comp content.

    `COMP_ICG_BODY_FLAT` is `COMP_ICG_BODY` with its submodel resolved into it: it declares no comp package and has no comp element at all, and the round trip of it must write none either.
    """
    counts, differences = package_roundtrip(COMP_ICG_BODY_FLAT)
    assert [construct for construct in counts if construct.startswith("comp.")] == []

    assert _comp_differences(differences) == []


def _declares_comp(sbml_path: Path) -> bool:
    """Test whether libsbml reads a document as declaring the comp package.

    Args:
        sbml_path: path of the SBML file

    Returns:
        whether the document declares comp
    """
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    return doc.getPlugin("comp") is not None


def comp_cases() -> list[Path]:
    """Get every comp case of the vendored SBML test suite.

    The cases are not spelled out, as in `fbc_v1_cases`: every l3v2 case whose header names the comp namespace is a candidate, and libsbml decides which of them declares the package.

    Returns:
        the path of every l3v2 case which declares comp, by case
    """
    candidates: list[Path] = []
    for sbml_path in sorted(SEMANTIC_DIR.glob("*/*-sbml-l3v2.xml")):
        with sbml_path.open(encoding="utf-8") as f:
            if "/comp/version" in f.read(4000):
                candidates.append(sbml_path)
    return [path for path in candidates if _declares_comp(path)]


#: every comp case of the vendored SBML test suite, empty without the suite
COMP_CASES: list[Path] = comp_cases()

#: the comp differences a case of the SBML test suite keeps, by construct and
#: count, with the reason. Every comp case of the suite round trips with its
#: whole comp content, so this is empty; a case which loses something belongs
#: here with the reason rather than being skipped.
COMP_REMAINING: dict[str, dict[str, int]] = {}


@requires_testsuite
def test_the_comp_cases_of_the_suite_are_found() -> None:
    """Test that the sweep below is parametrized with the comp cases.

    An empty parametrization is a single skip, so a sweep which found no case would pass without testing anything.
    """
    assert len(COMP_CASES) >= 100
    assert {path.name[:5] for path in COMP_CASES} >= {"01124", "01132", "01778"}
    assert set(COMP_REMAINING) <= {path.name[:5] for path in COMP_CASES}


@requires_testsuite
@pytest.mark.parametrize("sbml_path", COMP_CASES, ids=fixture_idfn)
def test_roundtrip_preserves_the_comp_content_of_every_case(
    sbml_path: Path, tmp_path: Path
) -> None:
    """Test that a round trip of a comp case of the SBML test suite loses no comp content.

    Every case is asserted to have comp content first, so preserving it cannot mean that the case has none, and every comp difference is asserted by construct and count, so content the round trip adds fails the case too. A case which cannot be preserved completely is not skipped: what remains of it is named in `COMP_REMAINING` with the reason.
    """
    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
    counts = _expected_constructs(comparable_document(doc_in))
    comp_constructs = {
        construct: count
        for construct, count in counts.items()
        if construct.startswith("comp.") and construct != "comp.package"
    }
    assert comp_constructs, f"'{sbml_path.name}' has no comp content"

    remaining = Counter(
        d.construct
        for d in diff_snapshots(*snapshots(doc_in, doc_out))
        if d.package == "comp"
    )

    assert dict(remaining) == COMP_REMAINING.get(sbml_path.name[:5], {}), (
        _comp_differences(structural_diff(doc_in, doc_out))
    )


def test_roundtrip_of_an_l3v1_comp_model_validates_at_its_own_version(
    tmp_path: Path,
) -> None:
    """Test what libsbml makes of an external model definition of another version.

    `COMP_ICG_BODY` is an L3V1 document whose liver submodel is the L3V1 file `icg_liver.xml` next to it. Written at L3V1, with that file beside it, the round trip validates without an error. Written at L3V2, libsbml refuses to resolve the reference, error 1020304 (`External models must be L3`, whose message says the document found at the source "was not SBML Level 3 Version 1"), and the submodel which names it is then unresolvable as well, error 1020615: libsbml requires the referenced document at the level and version of the document which references it. The round trip preserves the reference and does not touch the file it names, so the level of the document written is what decides this, and a caller who needs the reference to resolve writes the level of the source.
    """
    shutil.copy(COMP_ICG_BODY.parent / "icg_liver.xml", tmp_path / "icg_liver.xml")
    model = sbml_to_model(COMP_ICG_BODY)
    errors: dict[int, list[int]] = {}
    for version in (1, 2):
        out = tmp_path / f"icg_body-l3v{version}.xml"
        create_model(
            model=model,
            filepath=out,
            sbml_level=3,
            sbml_version=version,
            validate=False,
        )
        # the document is held while its errors are read: a libsbml error
        # does not keep the document it belongs to alive
        doc = _read(out)
        result = validate_doc(doc, options=ValidationOptions())
        errors[version] = sorted({error.getErrorId() for error in result.errors})

    assert errors[1] == []
    assert errors[2] == [1020304, 1020615]


def _key_value_pair_metadata_model() -> Model:
    """Get a model whose key-value pair states every field it can carry.

    `KeyValuePair.create_sbml` wrote the `key`, the `value` and the `uri` and
    never called `Sbase._set_fields`, so the id, name, metaid, sboTerm, notes
    and annotations of a pair were accepted and dropped. An fbc version 3
    `<fbc:keyValuePair>` carries all six, writes them and reads them back
    (measured with libsbml 5.21.2).

    Returns:
        the model definition
    """
    return Model(
        sid="key_value_pair_metadata",
        packages=[Package.FBC_V3],
        strict=False,
        parameters=[
            Parameter(
                sid="k",
                value=1.0,
                keyValuePairs=[
                    KeyValuePair(
                        key="kind",
                        value="test",
                        uri="https://example.org/keys",
                        sid="kvp1",
                        name="a key value pair",
                        metaId="meta_kvp1",
                        sboTerm="SBO:0000002",
                        notes=(
                            '<body xmlns="http://www.w3.org/1999/xhtml">'
                            "<p>a note of the pair</p></body>"
                        ),
                        annotations=[
                            (BQB.IS, "https://identifiers.org/chebi/CHEBI:15377")
                        ],
                    )
                ],
            )
        ],
    )


def _key_value_pair_metadata_sbml(tmp_path: Path) -> Path:
    """Write the key-value pair fixture as SBML L3V2.

    libsbml writes the `id` and the `name` of a `<fbc:keyValuePair>` into an
    L3V1 document as it does into an L3V2 one, but reads them back only from
    L3V2 (measured with libsbml 5.21.2), so the fixture is written at the
    level and version the round trip writes.

    Args:
        tmp_path: the directory the file is written to

    Returns:
        the path of the written SBML file
    """
    model = _key_value_pair_metadata_model()
    sbml_path = tmp_path / f"{model.sid}.xml"
    create_model(
        model=model,
        filepath=sbml_path,
        sbml_level=3,
        sbml_version=2,
        validate=False,
    )
    return sbml_path


def _key_value_pair(doc: libsbml.SBMLDocument) -> libsbml.KeyValuePair:
    """Get the single key-value pair of the parameter `k`.

    Args:
        doc: the document, which the caller holds

    Returns:
        the key-value pair of the parameter
    """
    plugin: libsbml.FbcSBasePlugin = doc.getModel().getParameter("k").getPlugin("fbc")
    return plugin.getKeyValuePair(0)


def test_key_value_pair_writes_every_field_it_can_carry(tmp_path: Path) -> None:
    """Test that the metadata of a key-value pair is written, not only its key."""
    sbml_path = _key_value_pair_metadata_sbml(tmp_path)
    doc = _read(sbml_path)

    pair = _key_value_pair(doc)
    assert (
        pair.getKey(),
        pair.getValue(),
        pair.getUri(),
        pair.getIdAttribute(),
        pair.getName(),
        pair.getMetaId(),
        pair.getSBOTermID(),
    ) == (
        "kind",
        "test",
        "https://example.org/keys",
        "kvp1",
        "a key value pair",
        "meta_kvp1",
        "SBO:0000002",
    )
    assert "a note of the pair" in pair.getNotesString()
    assert pair.getNumCVTerms() == 1


def test_roundtrip_preserves_the_metadata_of_a_key_value_pair(tmp_path: Path) -> None:
    """Test that the whole key-value pair survives a round trip.

    `structural_diff` compares the `key`, `value` and `uri` of a pair and the
    metadata of every element which has its own, so it sees each of the six
    fields.
    """
    sbml_path = _key_value_pair_metadata_sbml(tmp_path)
    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
    assert _expected_constructs(comparable_document(doc_in))["fbc.keyValuePair"] == 1

    diffs = [d for d in structural_diff(doc_in, doc_out) if d.package == "fbc"]

    assert [str(d) for d in diffs] == []
    assert _key_value_pair(doc_out).getName() == "a key value pair"


def _key_value_pair_model(packages: list[Package]) -> Model:
    """Get a model whose parameter and species reference carry key-value pairs.

    Args:
        packages: the packages the model declares

    Returns:
        the model
    """
    return Model(
        sid="key_value_pairs",
        name="a model with key-value pairs",
        packages=packages,
        compartments=[Compartment("c", 1.0, name="compartment")],
        species=[
            Species("S1", compartment="c", initialAmount=1.0, name="S1"),
            Species("S2", compartment="c", initialAmount=0.0, name="S2"),
        ],
        parameters=[
            Parameter(
                "k",
                1.0,
                name="k",
                keyValuePairs=[
                    KeyValuePair(key="kind", value="test", uri="https://example.org"),
                    KeyValuePair(key="other", value="42", uri=None),
                ],
            )
        ],
        reactions=[
            Reaction(
                "R1",
                ReactionEquation(
                    reactants=[
                        EquationPart(
                            species="S1",
                            stoichiometry=1.0,
                            keyValuePairs=[
                                KeyValuePair(key="reactant-key", value="47", uri=None)
                            ],
                        )
                    ],
                    products=[EquationPart(species="S2", stoichiometry=1.0)],
                ),
                name="reaction",
            )
        ],
    )


def test_key_value_pairs_of_an_fbc_v2_document_are_reported_and_not_written(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that an fbc version 2 document gets no key-value pair at all.

    A `<fbc:keyValuePair>` is fbc version 3. In an fbc version 2 document
    libsbml creates the element and answers every one of `setKey`,
    `setValue`, `setUri`, `setId` and `setName` with
    `LIBSBML_UNEXPECTED_ATTRIBUTE`, so what used to be written was an
    `<fbc:listOfKeyValuePairs>` of empty `<fbc:keyValuePair/>` elements, one
    per pair, with two or three `check()` errors each and nothing saying
    which element or which version was the problem.
    """
    model = _key_value_pair_model([Package.FBC_V2])
    sbml_path = tmp_path / f"{model.sid}.xml"
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        create_model(model=model, filepath=sbml_path, validate=False)

    sbml = sbml_path.read_text(encoding="utf-8")
    assert "keyValuePair" not in sbml
    assert "listOfKeyValuePairs" not in sbml

    errors = [record.getMessage() for record in caplog.records]
    assert len(errors) == 2, errors
    assert "2 key-value pair(s)" in errors[0]
    assert "Parameter(k" in errors[0]
    assert "fbc version 3" in errors[0] and "fbc version 2" in errors[0]
    assert "1 key-value pair(s)" in errors[1]
    assert "EquationPart(species='S1'" in errors[1]


def test_key_value_pairs_of_an_fbc_v3_document_are_written(tmp_path: Path) -> None:
    """Test the positive control: fbc version 3 writes every pair."""
    model = _key_value_pair_model([Package.FBC_V3])
    sbml_path = tmp_path / f"{model.sid}.xml"
    create_model(model=model, filepath=sbml_path, validate=False)

    sbml = sbml_path.read_text(encoding="utf-8")
    assert sbml.count("<keyValuePair ") == 3
    assert 'key="kind"' in sbml
    assert 'key="reactant-key"' in sbml


def test_key_value_pairs_declare_the_fbc_package_they_need(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that a model with pairs and no `packages=` declares fbc itself.

    libsbml attaches no fbc plugin to an element of a document which does not
    declare the package, so writing a pair raised `AttributeError: 'NoneType'
    object has no attribute 'getListOfKeyValuePairs'` and no file was written
    at all. A model reads off the packages its content engages, so the pairs
    of a model which asks for no package declare fbc version 3 themselves.
    """
    model = _key_value_pair_model([])
    sbml_path = tmp_path / f"{model.sid}.xml"
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        create_model(model=model, filepath=sbml_path, validate=False)

    sbml = sbml_path.read_text(encoding="utf-8")
    assert "fbc/version3" in sbml
    assert sbml.count("<keyValuePair ") == 3
    assert [record.getMessage() for record in caplog.records] == []


def test_key_value_pairs_without_an_fbc_plugin_are_reported(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the report for an element which has no fbc plugin at all.

    A caller which writes an element onto a `libsbml.Model` of a document
    that does not declare fbc reaches `getPlugin("fbc")`, which answers
    `None`; the pairs are reported rather than raising an `AttributeError`.
    """
    doc: libsbml.SBMLDocument = libsbml.SBMLDocument(libsbml.SBMLNamespaces(3, 2))
    libsbml_model: libsbml.Model = doc.createModel()
    libsbml_model.setId("no_fbc")

    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        Parameter(
            "k",
            1.0,
            name="k",
            keyValuePairs=[KeyValuePair(key="kind", value="test", uri=None)],
        ).create_sbml(libsbml_model)

    errors = [record.getMessage() for record in caplog.records]
    assert len(errors) == 1, errors
    assert "does not declare the fbc package" in errors[0]
    assert "Parameter(k" in errors[0]
    assert "keyValuePair" not in libsbml.writeSBMLToString(doc)


def _user_defined_constraint_model(packages: list[Package]) -> Model:
    """Get a model with one user defined constraint.

    Args:
        packages: the packages the model declares

    Returns:
        the model
    """
    return Model(
        sid="user_defined_constraints",
        name="a model with a user defined constraint",
        packages=packages,
        compartments=[Compartment("c", 1.0, name="compartment")],
        species=[
            Species("S1", compartment="c", initialAmount=1.0, name="S1"),
            Species("S2", compartment="c", initialAmount=0.0, name="S2"),
        ],
        parameters=[
            Parameter("lb", -1000.0, name="lower bound"),
            Parameter("ub", 1000.0, name="upper bound"),
            Parameter("k", 1.0, name="k"),
        ],
        reactions=[Reaction("R1", "S1 -> S2", name="reaction")],
        user_defined_constraints=[
            UserDefinedConstraint(
                sid="udc1",
                name="user defined constraint",
                lowerBound="lb",
                upperBound="ub",
                components=[
                    UserDefinedConstraintComponent(
                        variable="R1", coefficient="k", sid="udcc1", name="component"
                    )
                ],
            )
        ],
    )


def test_user_defined_constraints_of_an_fbc_v2_document_are_reported(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that an fbc version 2 document gets no user defined constraint.

    An `<fbc:userDefinedConstraint>` is fbc version 3. In an fbc version 2
    document libsbml creates the element and answers every one of
    `setUpperBound`, `setLowerBound`, `setVariable`, `setCoefficient` and
    `setVariableType` with `LIBSBML_UNEXPECTED_ATTRIBUTE`, so what was
    written was an empty `<fbc:userDefinedConstraint/>`, which is invalid.
    """
    model = _user_defined_constraint_model([Package.FBC_V2])
    sbml_path = tmp_path / f"{model.sid}.xml"
    with caplog.at_level(logging.ERROR, logger="sbmlutils"):
        create_model(model=model, filepath=sbml_path, validate=False)

    sbml = sbml_path.read_text(encoding="utf-8")
    assert "userDefinedConstraint" not in sbml
    errors = [record.getMessage() for record in caplog.records]
    assert len(errors) == 1, errors
    assert "1 user defined constraint(s)" in errors[0]
    assert "fbc version 3, the document is fbc version 2" in errors[0]


def test_user_defined_constraints_of_an_fbc_v3_document_are_written(
    tmp_path: Path,
) -> None:
    """Test the positive control: fbc version 3 writes the constraint."""
    model = _user_defined_constraint_model([Package.FBC_V3])
    sbml_path = tmp_path / f"{model.sid}.xml"
    create_model(model=model, filepath=sbml_path, validate=False)

    sbml = sbml_path.read_text(encoding="utf-8")
    assert "<fbc:userDefinedConstraint " in sbml
    assert 'fbc:lowerBound="lb"' in sbml
