"""Tests of the structural comparison which the package round trip is judged by.

A round trip of the fbc, distrib and comp packages is checked by `structural_diff` of `tests/structural.py`, since simulation and validation are both blind to these packages, see its docstring for the comparison policy. A comparison which reports nothing on a damaged document is blind as well, so these tests prove it sees each kind of loss: they damage one construct in a copy of a real fixture and assert that exactly that construct is reported, and they assert that an undamaged document is reported as unchanged.

They never assert what `sbml_to_model` loses today. Those losses are removed one by one by the tasks which follow, and a test pinned to them would break with every fix. The losses of the current parser are measured by `scripts/package_report.py` instead.

The cases of the SBML test suite are resolved from the checkout, see `tests/test_roundtrip.py`, since the installed package does not contain them.
"""

import logging
import re
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
    create_model,
)
from sbmlutils.resources import (
    COMP_ICG_BODY,
    EXAMPLES_DIR,
    FBC_ECOLI_CORE_SBML,
    FBC_RECON3D_SBML,
)
from sbmlutils.validation import ValidationOptions, validate_doc

#: the uncertainties of distrib, with parameters, spans and math
UNCERTAINTY_SBML: Path = RESOURCES_DIR / "distrib" / "uncertainty.xml"
#: the distributions of distrib, as csymbols in the math of initial assignments
DISTRIB_ALL_SBML: Path = RESOURCES_DIR / "distrib" / "distrib_all.xml"
#: gene product associations whose `and` and `or` nodes carry an sboTerm, and an
#: uncertainty
ECOLI_EXPRESSION_SBML: Path = RESOURCES_DIR / "distrib" / "e_coli_core_expression.xml"
#: the only user-defined constraints of the repository
FBC_UDC_SBML: Path = EXAMPLES_DIR / "fbc_user_defined_constraints.xml"


#: the source of a fixture: an SBML file, or a model definition built on demand
Source = Path | Callable[[], Model]


def _kvp_model() -> Model:
    """Get the model of the key-value pair example.

    The packaged `fbc/fbc_key_value_pair.xml` holds three `keyValuePair` elements without a key, value or uri, it predates the writer of key-value pairs. The example itself writes complete ones, so the fixture is created from it.

    The example is imported here and not at the top of the module, so that a broken example fails the one test which uses it instead of the collection of every test of this module.

    Returns:
        the model definition of the example
    """
    from examples.fbc.fbc_key_value_pair import model

    return model


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
        _kvp_model, _change_key_value_pair, "fbc.keyValuePair"
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
# the fbc round trip
# ---------------------------------------------------------------------------
#: the construct census of a fixture and the fbc differences of its round trip
Comparison = tuple[Counter[str], list[Difference]]


@pytest.fixture(scope="module")
def fbc_roundtrip(
    tmp_path_factory: pytest.TempPathFactory,
) -> Callable[[Path], Comparison]:
    """Round trip a fixture and compare its fbc content, once per fixture.

    The tests below assert on one construct of a fixture each, and the round trip of `FBC_RECON3D_SBML` takes about ten seconds, so every fixture is round tripped once and its result is cached for the module. The differences come from `snapshots`, which is the comparison policy, and the census which proves a fixture has a construct is an independent recount of the same document. The cache holds plain values only: the documents are released when the comparison returns, and a libsbml object does not keep its document alive.

    Args:
        tmp_path_factory: pytest's factory of the directory the round trips write to

    Returns:
        a function which round trips an SBML file and returns how many elements of every construct libsbml reads from it, counted independently of `snapshot`, and every difference of its fbc content
    """
    tmp_path = tmp_path_factory.mktemp("fbc-roundtrip")
    cache: dict[Path, Comparison] = {}

    def compare(sbml_path: Path) -> Comparison:
        if sbml_path not in cache:
            doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
            differences = diff_snapshots(*snapshots(doc_in, doc_out))
            cache[sbml_path] = (
                _expected_constructs(comparable_document(doc_in)),
                [d for d in differences if d.package == "fbc"],
            )
        return cache[sbml_path]

    return compare


def _assert_preserved(comparison: Comparison, *constructs: str) -> None:
    """Assert that a fixture has each construct and that the round trip changes none.

    Args:
        comparison: the census and the differences of a fixture, see `fbc_roundtrip`
        constructs: the constructs which have to be preserved
    """
    counts, differences = comparison
    assert [c for c in constructs if not counts[c]] == [], (
        f"the fixture has none of these constructs, so preserving them says "
        f"nothing: {[c for c in constructs if not counts[c]]}"
    )
    assert [str(d) for d in differences if d.construct in constructs] == []


def test_roundtrip_preserves_gene_products(
    fbc_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the gene products of a model and its associations survive a round trip.

    `FBC_ECOLI_CORE_SBML` has 137 gene products, every one of them annotated, and 69 reactions with a gene product association.
    """
    counts, _ = fbc_roundtrip(FBC_ECOLI_CORE_SBML)
    assert counts["fbc.geneProduct"] == 137
    assert counts["fbc.geneProductAssociation"] == 69

    _assert_preserved(
        fbc_roundtrip(FBC_ECOLI_CORE_SBML),
        "fbc.geneProduct",
        "fbc.geneProductAssociation",
    )


def test_roundtrip_preserves_objectives(
    fbc_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the objective of a model and its flux objectives survive a round trip.

    `FBC_ECOLI_CORE_SBML` maximizes the biomass reaction, which is the one thing an FBA model is run for.
    """
    counts, _ = fbc_roundtrip(FBC_ECOLI_CORE_SBML)
    assert counts["fbc.objective"] == 1
    assert counts["fbc.fluxObjective"] == 1

    _assert_preserved(
        fbc_roundtrip(FBC_ECOLI_CORE_SBML), "fbc.objective", "fbc.fluxObjective"
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
    fbc_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the flux bounds, charges and chemical formulas of a model survive.

    The flux bounds of `FBC_ECOLI_CORE_SBML` are what makes its flux space finite; 72 of its 72 species carry a charge and a chemical formula.
    """
    counts, _ = fbc_roundtrip(FBC_ECOLI_CORE_SBML)
    assert counts["fbc.fluxBound"] == 95
    assert counts["fbc.charge"] == 72
    assert counts["fbc.chemicalFormula"] == 72

    _assert_preserved(
        fbc_roundtrip(FBC_ECOLI_CORE_SBML),
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
    fbc_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the flux bounds of an fbc version 1 document survive a round trip.

    fbc version 1 states a bound as an `fbc:fluxBound` element of the model rather than as a parameter the reaction references, and there is no `Model` field for that element. The parser converts an fbc version 1 document with libsbml's own `convert fbc v1 to fbc v2` converter before reading it, which is exactly how `tests/structural.py` compares such a document: every bound becomes a parameter of the generated id `fb_<reaction>_<operation>`, which the reaction references.
    """
    sbml_path = testsuite_case("01186")
    doc = _read(sbml_path)
    fbc_v1: libsbml.FbcModelPlugin = doc.getModel().getPlugin("fbc")
    assert fbc_v1.getPackageVersion() == 1
    assert fbc_v1.getNumFluxBounds() == 52

    counts, _ = fbc_roundtrip(sbml_path)
    assert counts["fbc.fluxBound"] == 26

    _assert_preserved(fbc_roundtrip(sbml_path), "fbc.fluxBound")


def test_roundtrip_preserves_user_defined_constraints(
    fbc_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that the user-defined constraints of a model survive a round trip.

    A user-defined constraint is an fbc version 3 constraint which is not implied by the stoichiometry of the network; `FBC_UDC_SBML` is the only fixture of the repository which has any.
    """
    counts, _ = fbc_roundtrip(FBC_UDC_SBML)
    assert counts["fbc.userDefinedConstraint"] == 2
    assert counts["fbc.userDefinedConstraintComponent"] == 4

    _assert_preserved(
        fbc_roundtrip(FBC_UDC_SBML),
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

    A key-value pair of fbc version 3 sits on any element; the example puts one on the model, a parameter and a species. The fixture is built from the example, see `_kvp_model`.
    """
    sbml_path = _source_path(_kvp_model, tmp_path)
    doc_in, doc_out = roundtrip_document(sbml_path, tmp_path)
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
    assert _expected_constructs(comparable_document(doc_in))["fbc.keyValuePair"] == 1

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
    assert reactant_plugin.getNumKeyValuePairs() == 0
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
    fbc_roundtrip: Callable[[Path], Comparison],
) -> None:
    """Test that a round trip of an fbc fixture changes no fbc content at all.

    Between them the three fixtures carry every fbc construct the parser reads: `FBC_RECON3D_SBML` is the largest model of the repository with 2248 gene products, 10600 flux bounds and 5835 charges, and `FBC_UDC_SBML` is the only one with user-defined constraints. This asserts on every difference, not on the named constructs only, so a construct the round trip *adds* fails it too.
    """
    counts, differences = fbc_roundtrip(sbml_path)
    assert [c for c in constructs if not counts[c]] == []

    assert [str(d) for d in differences] == []


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
