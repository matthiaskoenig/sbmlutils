"""Tests of the structural comparison which the package round trip is judged by.

A round trip of the fbc, distrib and comp packages is checked by `structural_diff` of `tests/structural.py`, since simulation and validation are both blind to these packages, see its docstring for the comparison policy. A comparison which reports nothing on a damaged document is blind as well, so these tests prove it sees each kind of loss: they damage one construct in a copy of a real fixture and assert that exactly that construct is reported, and they assert that an undamaged document is reported as unchanged.

They never assert what `sbml_to_model` loses today. Those losses are removed one by one by the tasks which follow, and a test pinned to them would break with every fix. The losses of the current parser are measured by `scripts/package_report.py` instead.

The cases of the SBML test suite are resolved from the checkout, see `tests/test_roundtrip.py`, since the installed package does not contain them.
"""

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
    WHITELIST,
    Difference,
    Normalization,
    comparable_document,
    roundtrip_document,
    snapshot,
    structural_diff,
)
from test_roundtrip import testsuite_case

from sbmlutils import RESOURCES_DIR
from sbmlutils.factory import Model, create_model
from sbmlutils.resources import COMP_ICG_BODY, EXAMPLES_DIR, FBC_ECOLI_CORE_SBML

#: the uncertainties of distrib, with parameters, spans and math
UNCERTAINTY_SBML: Path = RESOURCES_DIR / "distrib" / "uncertainty.xml"
#: the distributions of distrib, as csymbols in the math of initial assignments
DISTRIB_ALL_SBML: Path = RESOURCES_DIR / "distrib" / "distrib_all.xml"
#: gene product associations whose `and` and `or` nodes carry an sboTerm, and an
#: uncertainty
ECOLI_EXPRESSION_SBML: Path = RESOURCES_DIR / "distrib" / "e_coli_core_expression.xml"
#: the only user-defined constraints of the repository
FBC_UDC_SBML: Path = EXAMPLES_DIR / "fbc_user_defined_constraints.xml"


def _kvp_model() -> Model:
    """Get the model of the key-value pair example.

    The packaged `fbc/fbc_key_value_pair.xml` holds three `keyValuePair` elements without a key, value or uri, it predates the writer of key-value pairs. The example itself writes complete ones, so the fixture is created from it.

    Returns:
        the model definition of the example
    """
    from examples.fbc.fbc_key_value_pair import model

    return model


def _source_path(source: Path | Model, tmp_path: Path) -> Path:
    """Resolve the source of a fixture to an SBML file.

    Args:
        source: an SBML file, or a model definition which is created first
        tmp_path: directory a model definition is created in

    Returns:
        the path of the SBML file
    """
    if isinstance(source, Path):
        return source
    sbml_path = tmp_path / f"{source.sid}.xml"
    create_model(model=source, filepath=sbml_path, validate=False)
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
    # fbc v3 references a parameter as the coefficient, the fixture spells a number
    assert component.getCoefficient() == "1"
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
        source: the fixture, an SBML file or a model definition
        damage: damages a document read from the source, in place
        constructs: the constructs which the damage changes, and nothing else
    """

    source: Path | Model
    damage: Callable[[libsbml.SBMLDocument], None]
    constructs: frozenset[str]


def _mutation(
    source: Path | Model,
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
        _kvp_model(), _change_key_value_pair, "fbc.keyValuePair"
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


@pytest.mark.parametrize("mutation", MUTATIONS)
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


def fixture_idfn(sbml_path: Path) -> str:
    """Name a test by its fixture."""
    return sbml_path.name


@pytest.mark.parametrize("sbml_path", FIXTURES, ids=fixture_idfn)
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


@pytest.mark.parametrize("sbml_path", FIXTURES, ids=fixture_idfn)
def test_snapshot_sees_every_element(sbml_path: Path) -> None:
    """Test that the comparison sees every package element libsbml reads.

    The snapshot is recounted from `getListOfAllElements`, which walks the whole document, so an element kind or a list the comparison forgot to walk is found here.
    """
    doc = comparable_document(_read(sbml_path))

    seen = Counter(construct for construct, _ in snapshot(doc))

    assert seen == _expected_constructs(doc)


#: the start tag of an element and its attributes, as libsbml writes them
_START_TAG = re.compile(r"<[^\s>/]+((?:\s+[^\s=]+=\"[^\"]*\")*)\s*/?>")
_ATTRIBUTE = re.compile(r"([^\s=]+)=\"[^\"]*\"")


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
    for name in _ATTRIBUTE.findall(match.group(1)):
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


@pytest.mark.parametrize("sbml_path", FIXTURES, ids=fixture_idfn)
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

    converted = comparable_document(doc)

    assert (converted.getLevel(), converted.getVersion()) == (3, 2)
    assert (doc.getLevel(), doc.getVersion()) == (3, 1), "the original was converted"
    assert snapshot(converted) == snapshot(doc)


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
    assert snap[("fbc.strict", "model")] == {"strict": True}


def test_roundtrip_document_returns_both_documents(tmp_path: Path) -> None:
    """Test that a round trip returns the document read and the one written."""
    doc_in, doc_out = roundtrip_document(UNCERTAINTY_SBML, tmp_path)

    assert doc_in.getModel() is not None
    assert doc_out.getModel() is not None
    assert (doc_out.getLevel(), doc_out.getVersion()) == (3, 2)
    assert isinstance(structural_diff(doc_in, doc_out), list)


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
    assert [entry.name for entry in WHITELIST] == [
        "gpa-flattening",
        "cn-integer",
        "miriam-urn",
    ]
    for entry in WHITELIST:
        assert len(entry.reason) > 40, entry.name


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


@pytest.mark.parametrize("urn", _URNS)
def test_miriam_urn_is_what_pymetadata_does(urn: str) -> None:
    """Test the URN normalization against the canonicalization of pymetadata.

    `create_model` writes a resource as pymetadata normalizes it, so the whitelist entry has to accept what pymetadata writes for a URN.
    """
    url = RDFAnnotation(BQB.IS, urn, validate=False).resource_normalized
    before = (("bqbiol:is", urn),)

    assert url is not None and url.startswith("https://identifiers.org/")
    assert _normalization("miriam-urn").equivalent(before, (("bqbiol:is", url),))


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
        # pymetadata writes a URN of an unknown collection as its bare term
        (("bqbiol:is", "urn:miriam:foo:bar"), ("bqbiol:is", "bar")),
        # a classic identifiers.org URL is not a URN
        (
            ("bqbiol:is", "http://identifiers.org/chebi/CHEBI:33699"),
            ("bqbiol:is", "https://identifiers.org/CHEBI:33699"),
        ),
        # http instead of https
        (
            ("bqbiol:is", "urn:miriam:uniprot:P03023"),
            ("bqbiol:is", "http://identifiers.org/uniprot:P03023"),
        ),
    ],
)
def test_miriam_urn_is_narrow(before: tuple[str, str], after: tuple[str, str]) -> None:
    """Test that the URN normalization accepts nothing but a URN written as its URL."""
    assert not _normalization("miriam-urn").equivalent((before,), (after,))


def test_miriam_urn_needs_every_resource_matched() -> None:
    """Test that a resource lost next to a normalized one is not accepted."""
    before = (
        ("bqbiol:is", "urn:miriam:uniprot:P03023"),
        ("bqbiol:is", "urn:miriam:uniprot:P03024"),
    )
    after = (("bqbiol:is", "https://identifiers.org/uniprot:P03023"),)

    assert not _normalization("miriam-urn").equivalent(before, after)
    assert not _normalization("miriam-urn").equivalent(after, before)


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
    for doc, resource in [
        (doc_in, "urn:miriam:uniprot:P0A9Q7"),
        (doc_out, "https://identifiers.org/uniprot:P0A9Q7"),
    ]:
        term = libsbml.CVTerm(libsbml.BIOLOGICAL_QUALIFIER)
        term.setBiologicalQualifierType(libsbml.BQB_IS_ENCODED_BY)
        term.addResource(resource)
        target: libsbml.GeneProduct = _fbc(doc).getGeneProduct("G_b1241")
        assert target.addCVTerm(term) == libsbml.LIBSBML_OPERATION_SUCCESS
    assert gene_product.getNumCVTerms() == 2

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


def test_difference_names_its_package() -> None:
    """Test that a difference names the package of its construct."""
    difference = Difference("comp.modelDefinition.species", "x", "name", "a", "b")

    assert difference.package == "comp"
    assert "comp.modelDefinition.species" in str(difference)
