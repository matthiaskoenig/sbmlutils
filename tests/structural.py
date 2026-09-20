"""Structural comparison of the fbc, distrib and comp content of two SBML documents.

A round trip `SBML -> sbml_to_model -> create_model -> SBML` of a document which uses the fbc, distrib or comp package cannot be checked by simulation or by validation: roadrunner refuses to simulate fbc, ignores distrib and flattens comp, and a document stripped of all three packages validates without an error. `structural_diff` is the check which sees such a loss: it compares the package content of the document read with the package content of the document written, attribute by attribute, and returns every difference, see https://github.com/matthiaskoenig/sbmlutils/issues/469. It returns differences, it never asserts; the tests and `scripts/package_report.py` decide what a difference means.

This docstring is the comparison policy. The code implements it and nothing else, and every package round-trip test is judged by it.

## The documents compared

The round trip writes SBML L3V2 with fbc version 2 or 3, so a document read at another version cannot come back unchanged, only as it reads when converted. Each document is therefore first brought to L3V2 and fbc version 2 or higher, on a copy, by libsbml's own converters, which are the reference for that conversion: the `convert fbc v1 to fbc v2` converter with its default options for fbc version 1, then `setLevelAndVersion(3, 2, strict=False)` for any other level and version. A document already at those versions is compared as it is.

- The fbc v1 conversion turns every `fbc:fluxBound` into a `fbc:lowerFluxBound`/`fbc:upperFluxBound` reference to a new parameter with the generated id `fb_<reaction>_<operation>`. A round trip of an fbc v1 document is expected to reproduce exactly that. The converter drops the `<fbc:fluxBound>` element, and both documents are compared as libsbml converts them, so the `metaid`, the `sboTerm` and the annotation of that element are invisible on both sides: what survives of it is the bound it expresses, `fbc.fluxBound`, and the parameter the conversion generates for it.
- **`fbc.strict` is not compared when the source document declares fbc v1**, and that is the only thing the fbc v1 conversion is not taken at its word for. fbc v1 has no `strict` attribute, so the source says nothing about it; the converter nevertheless sets `fbc:strict="true"` on every v1 document, flux bounds or not, which is its own invention. It is a claim with consequences: a strict model requires the `constant` attribute of every species reference to be `true`, and 11 of the 12 fbc v1 cases of the SBML test suite are valid as they are and become invalid under it, with 54 errors of libsbml id 2020714 (`SpeciesReferences must be constant when strict`) each. A round trip must not turn a valid model into an invalid one, so it writes `fbc:strict="false"` for such a document, the weakest claim, and this comparison holds neither side to the converter's `true`. Everything else about an fbc v1 document is compared as usual, `fbc.fluxBound` included. This is not a whitelist entry: the whitelist declares two values of a compared attribute the same, whereas this construct is not compared at all for such a source, and it is keyed on the source document rather than on a pair of values. The version has to be read from the source before `comparable_document` converts it, which is what `compares_fbc_strict` is for.
- The L3V1 to L3V2 conversion removes the `fast` attribute of a reaction, which L3V2 does not have, and changes no package content (measured on every L3V1 fixture of the corpus).

## Snapshot, construct and element id

A document is reduced to a snapshot: a mapping from `(construct, element id)` to the attributes of one element, which are plain python values. The construct names the kind of content, prefixed by its package: `fbc.geneProduct`, `distrib.uncertainty`, `comp.port`. The element id is the path of the element from its model, one segment per element: `model/reaction:R_PFK`, `modelDefinition:md1/port:p1/sBaseRef/sBaseRef`, `model/parameter:p1/uncertainty#0/uncertParameter#2`. The main model is `model`, a model definition is `modelDefinition:<id>`, and the package declarations of the document are `document`.

A segment is `<element>:<id>` for an element with a required id, `<element>[<reference>]` for an element identified by what it references (a flux objective by its reaction, a key-value pair by its key, a replaced element by its submodel and target, a species reference by its role, `reactant`, `product` or `modifier`, and its species), `<element>` for the single child of its kind (a kinetic law, a trigger, a replaced by, an `sBaseRef`), and `<element>#<position>` where the position is the identity (see Order). A segment which repeats among the children of one element gets `#1`, `#2` and so on appended for its second, third and later occurrence.

Two snapshots are compared key by key. An element on one side only is one difference with the attribute `*`, whose other side is `ABSENT`. An element on both sides is compared attribute by attribute, and an attribute whose values differ is a difference, unless an entry of `WHITELIST` declares the two values the same. Nothing else is ever treated as equal.

## What is compared

Every construct also compares the metadata of its element, where the element has its own: `id`, `name`, `metaId`, `sboTerm`, `cvterms` (the set of `(qualifier, resource)` pairs of its RDF annotation) and `notes`. The constructs which are attributes of a core element (`fbc.strict`, `fbc.fluxBound`, `fbc.charge`, `fbc.chemicalFormula`, `distrib.csymbol`) have no metadata of their own; the metadata of that core element is core content.

### fbc

- `fbc.package` (the document): the declared package `version` and `required`.
- `fbc.strict` (a model): `strict`, except for a source which declares fbc v1, see above.
- `fbc.geneProduct`: `label`, `associatedSpecies`.
- `fbc.objective`: `type`, and `active`, whether it is the `activeObjective` of the list of objectives.
- `fbc.fluxObjective` (under its objective): `reaction`, `coefficient`, and the fbc v3 `reaction2` and `variableType`.
- `fbc.fluxBound` (a reaction with a bound): `lowerFluxBound`, `upperFluxBound`, the ids of the bound parameters, and `lowerValue`, `upperValue`, the values of those parameters. A parameter is core content, but the value is what the bound means, and for an fbc v1 document it is the `fbc:value` of its `fbc:fluxBound`, which the conversion moves into the parameter: without it, a changed fbc v1 bound would be invisible.
- `fbc.geneProductAssociation` (a reaction with one): `association`, the association as the infix string of gene product ids (`toInfix(usingId=True)`, the side `Reaction.geneProductAssociation` is written from), and `nodes`, the metadata of every `and`, `or` and `geneProductRef` node which carries any, in document order. The string cannot hold the metadata of a node, so a node's metadata is compared on its own.
- `fbc.charge`, `fbc.chemicalFormula` (a species): `charge`, `chemicalFormula`. The charge is read as libsbml writes it, the integer of fbc v2 and the double of fbc v3, as a float: libsbml keeps the two apart, and the getter of the other version returns 0.
- `fbc.userDefinedConstraint`: `lowerBound`, `upperBound`.
- `fbc.userDefinedConstraintComponent` (under its constraint): `coefficient`, `variable`, `variable2`, `variableType`.
- `fbc.keyValuePair` (under any element): `key`, `value`, `uri`.

### distrib

- `distrib.package` (the document): `version`, `required`.
- `distrib.uncertainty` (under any element): metadata only.
- `distrib.uncertParameter` (under an uncertainty, and nested under an uncertParameter): `element`, which is `uncertParameter` or `uncertSpan`, `type`, `value`, `var`, `units`, `definitionURL`, `math`, and for a span `valueLower`, `varLower`, `valueUpper`, `varUpper`. libsbml reads a span as a subclass of `UncertParameter` in the same list, so both are one construct and their order is compared across both.
- `distrib.csymbol` (any element whose math uses a distribution of distrib, a `csymbol` whose `definitionURL` starts with `http://www.sbml.org/sbml/symbols/distrib/`, on either side): `math`, the whole math of the element. A draw from a distribution is distrib content although it lives in core math: if a round trip reads `normal(0, 1)` back as a call of an undefined function `normal`, only this construct sees it.

### comp

- `comp.package` (the document): `version`, `required`.
- `comp.modelDefinition`: the model attributes `substanceUnits`, `timeUnits`, `volumeUnits`, `areaUnits`, `lengthUnits`, `extentUnits`, `conversionFactor`, and recursively everything in it: every package construct of this list, under the path of the model definition, and every core element as `comp.modelDefinition.<element>` with all its L3V2 core attributes and its math (see `_CORE_ATTRIBUTES`). The core content of the main model is not compared here, it is the subject of `tests/test_roundtrip.py`; the core content of a model definition is compared because nothing else sees it.
- `comp.externalModelDefinition`: `source`, `modelRef`, `md5`, and everything below it: an external model definition is an `SBase` and carries the children every element can have, its key-value pairs above all. The referenced file is not opened: an external model definition is a reference and is preserved as one.
- `comp.submodel`: `modelRef`, `timeConversionFactor`, `extentConversionFactor`, and `substanceConversionFactor`, which libsbml reads although comp version 1 does not define it.
- `comp.deletion` (under its submodel, where SBML places it): `portRef`, `idRef`, `unitRef`, `metaIdRef`.
- `comp.port`: `portRef`, `idRef`, `unitRef`, `metaIdRef`.
- `comp.replacedElement` (under any element): `submodelRef`, `deletion`, `conversionFactor`, `portRef`, `idRef`, `unitRef`, `metaIdRef`.
- `comp.replacedBy` (under any element): `submodelRef`, `portRef`, `idRef`, `unitRef`, `metaIdRef`.
- `comp.sBaseRef` (under a port, deletion, replaced element, replaced by or `sBaseRef`): `portRef`, `idRef`, `unitRef`, `metaIdRef`. Each level of a nested chain is one element under the level above it, so the whole chain is compared, level by level.

### Not compared

- The core content of the main model, see above.
- The containers `listOf...` themselves; the `activeObjective` of the list of objectives is compared as `fbc.objective.active`.
- The model history, the non-RDF content of an annotation, and nested CVTerms, none of which the parser reads (#416).
- Key-value pairs, uncertainties and replacements on the `and`, `or` and `geneProductRef` nodes of an association, which `Reaction.geneProductAssociation` cannot hold.
- Content of other packages (`groups`, `layout`, `render`, `qual`, ...), and anything libsbml does not read: an element in an unknown or draft syntax is gone before the comparison starts.

## Order

A list whose SBML order carries no meaning compares as a set: its elements are matched by id or by reference, see the segments above, so a reordering is no difference. These are all lists except three, which compare in order, by position, so that a reordering is a difference:

- the uncertainties of an element,
- the uncertParameters and uncertSpans of an uncertainty or of an uncertParameter,
- the levels of an `sBaseRef` chain, each of which is the single child of the level above.

Distrib gives an uncertainty and its parameters no required id and no reference to match them by, so their position is their only identity.

Order carries no meaning in a list of algebraic rules, constraints or events without an id either, but they have nothing else to be matched by, so they are matched by position too.

## How values are read

Through the libsbml getters, the `isSet` getter first: an unset attribute is `None`. A double is a python `float`, and two `NaN` are equal. Math is libsbml's MathML serialization of the AST (`writeMathMLToString`), notes are libsbml's serialization of the notes (`getNotesString`), and a CVTerm resource is the URI string as written. Enumerations are read as their string (`variableType`, the `type` of an uncertParameter), a unit kind as its name.

## The whitelist

`WHITELIST` holds the three normalizations of R5 of the design spec and nothing else. Each is known to preserve the meaning, and each is narrow: it accepts exactly its normalization of a value and rejects that normalization combined with any other change. Each entry is keyed by the construct and the attribute it applies to, never by the attribute alone, so that a construct which gains an attribute of the same name does not inherit a normalization of another construct; an entry whose construct is `None` applies to that attribute of every construct.

- `gpa-flattening` (`fbc.geneProductAssociation.association`): libsbml flattens a nested group of the same operator, `((a and b) and c)` is written back as `(a and b and c)`. Accepted when the association written parses to exactly the tree of the association read with every group spliced into its parent group of the same operator, and only that: the operands keep their order, no operand is added, removed or repeated, an operator is never changed, and a partly flattened or regrouped association is not accepted.
- `cn-integer` (any `math`): math round trips as an L3 infix string, which spells a real of integral value like an integer, so `<cn> 1 </cn>` is read back as `<cn type="integer"> 1 </cn>`. Accepted when both MathML trees are identical except for `cn` elements without a `type` whose value is a finite integral number, which come back with `type="integer"`, the same integer and otherwise the same attributes. A negative real read back as the unary minus of an integer is a different tree and is not accepted.
- `identifiers-org` (any `cvterms`): pymetadata canonicalizes an annotation resource to the compact identifiers.org URL of its collection and term, `urn:miriam:chebi:CHEBI%3A33699` and `http://identifiers.org/chebi/CHEBI:12965` as `https://identifiers.org/CHEBI:33699` and `https://identifiers.org/CHEBI:12965`. **The entry is defined by its result**, and the source is one of four forms, each of them measured against pymetadata:

    1. a MIRIAM URN, `urn:miriam:<collection>:<term>`,
    2. a classic identifiers.org URL, `http(s)://identifiers.org/<collection>/<term>`,
    3. the `http` spelling of the compact URL, `http://identifiers.org/BTO:0000131`,
    4. a bare compact identifier, `UO:0000021`.

  Accepted when every resource which differs is one of those on one side and on the other side exactly `https://identifiers.org/<collection>:<term>`, or `https://identifiers.org/<term>` if the term carries the collection as its own prefix, with the same qualifier, the term unchanged except for the `%3A` of a URN decoded to `:`, and the collection unchanged except for the two legacy renames pymetadata applies, `obo.go` to `go` and `biomodels.sbo` to `sbo`. A source of form 3 or 4 carries its collection as the prefix of its term already, so its only accepted result is the identifiers.org URI written in front of it, unchanged in prefix and term.

  A result which is not that compact URL is a loss and is never accepted, whichever form it came from: the bare term pymetadata writes for a collection its registry does not know, which carries neither the collection nor a URI scheme (`http://identifiers.org/sbmlutils.test.collection1/1406` as `1406`), a resource stripped of its collection, which pymetadata does for a term which does not match the pattern the registry gives its collection (`http://identifiers.org/chebi/000000035` as `https://identifiers.org/000000035`), and a term whose repeated collection prefix was shortened away.
"""

import math
import re
import xml.etree.ElementTree as ElementTree
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import libsbml

from sbmlutils.factory import create_model
from sbmlutils.parser import sbml_to_model

#: the packages compared
PACKAGES: tuple[str, ...] = ("fbc", "distrib", "comp")

#: the start of the `definitionURL` of every distribution of distrib
DISTRIB_CSYMBOL: str = "http://www.sbml.org/sbml/symbols/distrib/"

#: the attribute of a difference of a whole element, which exists on one side only
ELEMENT: str = "*"

#: the side of such a difference on which the element does not exist
ABSENT: str = "<absent>"

#: the attributes of an element and their values
Attributes = dict[str, object]

#: the attributes of every element of a document, by `(construct, element id)`
Snapshot = dict[tuple[str, str], Attributes]


@dataclass(frozen=True)
class Difference:
    """A difference in the package content of two documents.

    Attributes:
        construct: the kind of content, prefixed by its package, e.g. `fbc.geneProduct`
        element_id: the path of the element from its model, e.g. `model/geneProduct:G_b0001`
        attribute: the attribute which differs, `ELEMENT` if the element exists on one side only
        before: the value in the document read, `ABSENT` if the element does not exist there
        after: the value in the document written, `ABSENT` if the element does not exist there
    """

    construct: str
    element_id: str
    attribute: str
    before: object
    after: object

    @property
    def package(self) -> str:
        """Get the package of the construct, `fbc`, `distrib` or `comp`."""
        return self.construct.split(".")[0]

    def __str__(self) -> str:
        """Get the difference as a single line."""
        return (
            f"{self.construct} '{self.element_id}' {self.attribute}: "
            f"{self.before!r} -> {self.after!r}"
        )


@dataclass(frozen=True)
class Normalization:
    """A change of a value which is known to preserve its meaning, see the module docstring.

    Attributes:
        name: the name of the normalization
        construct: the construct it applies to, or `None` for every construct
        attribute: the attribute of that construct it applies to
        reason: why the normalized value means the same
        equivalent: whether the value read and the value written are that normalization of each other
    """

    name: str
    construct: str | None
    attribute: str
    reason: str
    equivalent: Callable[[Any, Any], bool]

    def applies_to(self, construct: str, attribute: str) -> bool:
        """Test whether this normalization applies to an attribute of a construct.

        An entry is keyed by its construct and its attribute, never by the attribute alone: a construct which gains an attribute of a name another construct normalizes must not inherit that normalization.

        Args:
            construct: the construct of the element, e.g. `fbc.geneProductAssociation`
            attribute: the attribute which differs, e.g. `association`

        Returns:
            whether the entry is the one of this attribute of this construct
        """
        if attribute != self.attribute:
            return False
        return self.construct is None or construct == self.construct


# ---------------------------------------------------------------------------
# gpa-flattening
# ---------------------------------------------------------------------------
#: a gene product association as a tree: a gene product id, or an operator with
#: its operands; the operator of a group of a single operand is `None`
_Association = str | tuple[str | None, tuple["_Association", ...]]

_ASSOCIATION_TOKEN = re.compile(r"\(|\)|[^\s()]+")


def _parse_association(infix: str) -> _Association | None:
    """Parse the infix string of a gene product association.

    Parentheses delimit a group, and a group mixes no operators, which is how libsbml writes an association. Parentheses around a single gene product are a group of one operand, whose operator is `None`, so that no such parenthesis is dropped silently; parentheses around a group are that group.

    Args:
        infix: the association, e.g. `((a and b) or c)`

    Returns:
        the tree of the association, `None` if it is no well formed association
    """
    tokens = _ASSOCIATION_TOKEN.findall(infix)
    position = 0

    def expression() -> _Association | None:
        nonlocal position
        operands = [operand()]
        operators: set[str] = set()
        while position < len(tokens) and tokens[position] in ("and", "or"):
            operators.add(tokens[position])
            position += 1
            operands.append(operand())
        if any(o is None for o in operands) or len(operators) > 1:
            return None
        if not operators:
            return operands[0]
        return (operators.pop(), tuple(o for o in operands if o is not None))

    def operand() -> _Association | None:
        nonlocal position
        if position >= len(tokens) or tokens[position] in (")", "and", "or"):
            return None
        token = tokens[position]
        position += 1
        if token != "(":
            return token
        inner = expression()
        if inner is None or position >= len(tokens) or tokens[position] != ")":
            return None
        position += 1
        return inner if isinstance(inner, tuple) and inner[0] else (None, (inner,))

    tree = expression()
    return tree if position == len(tokens) else None


def _flatten(tree: _Association) -> _Association:
    """Splice every group into its parent group of the same operator."""
    if isinstance(tree, str):
        return tree
    operator, operands = tree
    flat: list[_Association] = []
    for child in (_flatten(operand) for operand in operands):
        if operator is not None and isinstance(child, tuple) and child[0] == operator:
            flat.extend(child[1])
        else:
            flat.append(child)
    return (operator, tuple(flat))


def _gpa_flattening(before: object, after: object) -> bool:
    """Test whether an association was written back as its flattened form.

    Args:
        before: the association read
        after: the association written

    Returns:
        whether `after` is exactly `before` with its nested groups of the same operator spliced into their parent
    """
    if not isinstance(before, str) or not isinstance(after, str):
        return False
    tree_before = _parse_association(before)
    tree_after = _parse_association(after)
    if tree_before is None or tree_after is None:
        return False
    return tree_after == _flatten(tree_before)


# ---------------------------------------------------------------------------
# cn-integer
# ---------------------------------------------------------------------------
_MATHML_CN = "{http://www.w3.org/1998/Math/MathML}cn"


def _text(text: str | None) -> str:
    """Get the text of an XML node without its surrounding whitespace."""
    return (text or "").strip()


def _cn_gained_integer(before: ElementTree.Element, after: ElementTree.Element) -> bool:
    """Test whether a `cn` of a real of integral value came back as an integer.

    Args:
        before: the `cn` read
        after: the `cn` written

    Returns:
        whether `before` has no type, `after` has `type="integer"`, both have the same value and otherwise the same attributes
    """
    if "type" in before.attrib or after.attrib.get("type") != "integer":
        return False
    if {k: v for k, v in after.attrib.items() if k != "type"} != before.attrib:
        return False
    if len(before) or len(after) or _text(before.tail) != _text(after.tail):
        return False
    try:
        value = float(_text(before.text))
        integer = int(_text(after.text))
    except ValueError:
        return False
    return math.isfinite(value) and value.is_integer() and int(value) == integer


def _same_math(before: ElementTree.Element, after: ElementTree.Element) -> bool:
    """Test whether two MathML trees are equal but for `cn` elements gaining a type.

    Args:
        before: the MathML read
        after: the MathML written

    Returns:
        whether the trees are equal node by node, where a `cn` may differ only as `_cn_gained_integer` allows
    """
    if before.tag != after.tag or len(before) != len(after):
        return False
    if before.tag == _MATHML_CN and before.attrib != after.attrib:
        return _cn_gained_integer(before, after)
    if (
        before.attrib != after.attrib
        or _text(before.text) != _text(after.text)
        or _text(before.tail) != _text(after.tail)
    ):
        return False
    return all(_same_math(b, a) for b, a in zip(before, after, strict=True))


def _cn_integer(before: object, after: object) -> bool:
    """Test whether math came back with reals of integral value as integers.

    Args:
        before: the MathML read
        after: the MathML written

    Returns:
        whether the two are the same math but for `cn` elements gaining `type="integer"`
    """
    if not isinstance(before, str) or not isinstance(after, str):
        return False
    try:
        return _same_math(ElementTree.fromstring(before), ElementTree.fromstring(after))
    except ElementTree.ParseError:
        return False


# ---------------------------------------------------------------------------
# identifiers-org
# ---------------------------------------------------------------------------
#: a deprecated MIRIAM URN, `urn:miriam:<collection>:<term>`
_MIRIAM_URN = re.compile(r"urn:miriam:([^:]+):(.+)")

#: a classic identifiers.org URL, `http(s)://identifiers.org/<collection>/<term>`;
#: the collection is spelled as pymetadata's `IDENTIFIERS_ORG_PATTERN_CLASSIC`
#: spells it, which is why `http://identifiers.org/ec-code/1.1.1.1` is no classic
#: URL to pymetadata and comes back unchanged
_CLASSIC_URL = re.compile(r"https?://identifiers\.org/([a-zA-Z0-9.]+)/(.+)")

#: a compact identifier, `<prefix>:<term>`, as the `http` spelling of its
#: identifiers.org URL and bare; the term carries no `/`, so that an arbitrary
#: URL and a `<collection>/<term>` short form are no compact identifier
_COMPACT_URL = re.compile(r"https?://identifiers\.org/([a-zA-Z0-9.]+:[^/\s]+)")
_COMPACT_IDENTIFIER = re.compile(r"[a-zA-Z0-9.]+:[^/\s]+")

#: the collections pymetadata renames, see `RDFAnnotation.replaced_collections`
_LEGACY_COLLECTIONS: dict[str, str] = {"obo.go": "go", "biomodels.sbo": "sbo"}

#: the URI every canonicalized resource starts with, pymetadata's
#: `IDENTIFIERS_ORG_PREFIX`; a resource written without it carries no collection
#: and, as a bare term does, no URI scheme at all
_IDENTIFIERS_ORG: str = "https://identifiers.org/"


def _collection_and_term(resource: str) -> tuple[str, str] | None:
    """Split a resource which pymetadata canonicalizes into its collection and its term.

    Args:
        resource: a resource, e.g. `urn:miriam:chebi:CHEBI%3A33699` or `http://identifiers.org/chebi/CHEBI:12965`

    Returns:
        the collection, with the two legacy renames applied, and the term, with the `%3A` of a URN decoded; `None` for a resource which is neither a MIRIAM URN nor a classic identifiers.org URL
    """
    urn = _MIRIAM_URN.fullmatch(resource)
    url = _CLASSIC_URL.fullmatch(resource)
    if urn is not None:
        collection, term = urn.group(1), urn.group(2).replace("%3A", ":")
    elif url is not None:
        collection, term = url.group(1), url.group(2)
    else:
        return None
    return _LEGACY_COLLECTIONS.get(collection, collection), term


def _compact_identifier(resource: str) -> str | None:
    """Get the compact identifier a resource already is, `<prefix>:<term>`.

    These are the two source forms which carry their collection as the prefix of their term already, so that pymetadata only has to write the identifiers.org URI in front of them: the `http` spelling of the compact URL, `http://identifiers.org/BTO:0000131`, and the bare compact identifier, `UO:0000021`. A MIRIAM URN is one of the other two source forms and is never read as one of these.

    Args:
        resource: a resource, e.g. `http://identifiers.org/BTO:0000131` or `UO:0000021`

    Returns:
        the compact identifier, `None` if the resource is none
    """
    if resource.startswith("urn:"):
        return None
    url = _COMPACT_URL.fullmatch(resource)
    if url is not None:
        return url.group(1)
    return resource if _COMPACT_IDENTIFIER.fullmatch(resource) else None


def _normalized_forms(resource: str) -> set[str]:
    """Get the resources pymetadata's canonicalization may write for a resource.

    A resource which is a compact identifier already is written as the identifiers.org URI of exactly that identifier, or, for a collection its registry does not know, as the identifier alone. Otherwise pymetadata splits the resource into its collection and its term and writes the compact `https://identifiers.org/<collection>:<term>`, or `https://identifiers.org/<term>` where the term carries its collection as its own prefix, or again the bare `<term>`. Only the forms which keep the collection are a normalization, and `_identifiers_org` accepts only those: a form which drops it says something else than the resource read did.

    Args:
        resource: a resource, e.g. `urn:miriam:chebi:CHEBI%3A33699`

    Returns:
        the forms of the resource; empty for a resource which is none of the four source forms
    """
    compact = _compact_identifier(resource)
    if compact is not None:
        return {f"{_IDENTIFIERS_ORG}{compact}", compact}
    parsed = _collection_and_term(resource)
    if parsed is None:
        return set()
    collection, term = parsed
    forms = {f"{_IDENTIFIERS_ORG}{collection}:{term}", term}
    prefix, separator, _ = term.partition(":")
    if separator and prefix.lower() == collection.lower():
        forms.add(f"{_IDENTIFIERS_ORG}{term}")
    return forms


def _identifiers_org(before: object, after: object) -> bool:
    """Test whether annotations came back canonicalized as identifiers.org URLs.

    Args:
        before: the `(qualifier, resource)` pairs read
        after: the `(qualifier, resource)` pairs written

    Returns:
        whether every pair which differs is a MIRIAM URN or a classic identifiers.org URL read and written as its compact URL, with the same qualifier, one for one
    """
    if not isinstance(before, tuple) or not isinstance(after, tuple):
        return False
    unmatched_before = set(before) - set(after)
    unmatched_after = set(after) - set(before)
    if not unmatched_before:
        return False
    # every resource written has to be the compact identifiers.org URI of the one
    # read: the bare term pymetadata writes for a collection its registry does not
    # know, `1406` for a `<collection>/1406` of an unknown collection, carries
    # neither the collection nor a URI scheme, which is a loss and no normalization
    if any(
        not resource.startswith(_IDENTIFIERS_ORG) for _, resource in unmatched_after
    ):
        return False
    for qualifier, resource in sorted(unmatched_before):
        candidates = sorted(
            {(qualifier, form) for form in _normalized_forms(resource)}
            & unmatched_after
        )
        if not candidates:
            return False
        unmatched_after.remove(candidates[0])
    return not unmatched_after


#: the normalizations of R5 of the design spec, the only differences which are no
#: difference
WHITELIST: tuple[Normalization, ...] = (
    Normalization(
        name="gpa-flattening",
        construct="fbc.geneProductAssociation",
        attribute="association",
        reason=(
            "libsbml parses an association into a tree and splices a nested group "
            "into its parent group of the same operator, so ((a and b) and c) is "
            "written back as (a and b and c): and and or are associative, so the "
            "boolean rule is the same, see the pinned R_PFL and R_ATPS4r of e_coli_core"
        ),
        equivalent=_gpa_flattening,
    ),
    Normalization(
        name="cn-integer",
        construct=None,
        attribute="math",
        reason=(
            "math round trips as an L3 infix string, which spells a real of "
            "integral value like an integer, so <cn> 1 </cn> is read back as "
            '<cn type="integer"> 1 </cn>: the same number with the same unit'
        ),
        equivalent=_cn_integer,
    ),
    Normalization(
        name="identifiers-org",
        construct=None,
        attribute="cvterms",
        reason=(
            "create_model writes a resource as pymetadata canonicalizes it, which "
            "writes a MIRIAM URN, a classic identifiers.org URL, the http "
            "spelling of the compact URL and a bare compact identifier as the "
            "compact identifiers.org URL of the same collection and term, "
            "urn:miriam:chebi:CHEBI%3A33699, "
            "http://identifiers.org/chebi/CHEBI:12965 and UO:0000021 as "
            "https://identifiers.org/CHEBI:33699, "
            "https://identifiers.org/CHEBI:12965 and "
            "https://identifiers.org/UO:0000021: the same identifier, resolved by "
            "the same registry"
        ),
        equivalent=_identifiers_org,
    ),
)


# ---------------------------------------------------------------------------
# the documents compared
# ---------------------------------------------------------------------------
def comparable_document(doc: libsbml.SBMLDocument) -> libsbml.SBMLDocument:
    """Bring a document to the versions the round trip writes, see the module docstring.

    Args:
        doc: a document, which the caller holds and which is not changed

    Returns:
        the document itself if it is at L3V2 and fbc version 2 or higher, else a converted copy, which the caller has to hold for as long as it uses any object of it

    Raises:
        ValueError: if libsbml cannot convert the document
    """
    fbc: libsbml.SBMLDocumentPlugin | None = doc.getPlugin("fbc")
    fbc_v1 = fbc is not None and fbc.getPackageVersion() == 1
    other_level = (doc.getLevel(), doc.getVersion()) != (3, 2)
    if not fbc_v1 and not other_level:
        return doc

    converted: libsbml.SBMLDocument = doc.clone()
    if fbc_v1:
        properties = libsbml.ConversionProperties()
        properties.addOption("convert fbc v1 to fbc v2", True)
        status: int = converted.convert(properties)
        if status != libsbml.LIBSBML_OPERATION_SUCCESS:
            raise ValueError(f"libsbml cannot convert fbc v1 to fbc v2: {status}")
    if other_level and not converted.setLevelAndVersion(3, 2, False):
        raise ValueError(
            f"libsbml cannot convert L{doc.getLevel()}V{doc.getVersion()} to L3V2"
        )
    return converted


def compares_fbc_strict(doc: libsbml.SBMLDocument) -> bool:
    """Test whether `fbc.strict` is compared for a round trip of this source document.

    It is not for a source which declares fbc version 1, which has no `strict` attribute: the `fbc:strict="true"` such a document ends up with is the invention of libsbml's converter, see the module docstring. The version has to be read here, from the source, since `comparable_document` converts it away.

    Args:
        doc: the document read, before it is converted; the caller holds it

    Returns:
        whether the `fbc.strict` of the two documents is compared
    """
    fbc: libsbml.SBMLDocumentPlugin | None = doc.getPlugin("fbc")
    return fbc is None or fbc.getPackageVersion() != 1


def roundtrip_document(
    sbml_path: Path, tmp_path: Path
) -> tuple[libsbml.SBMLDocument, libsbml.SBMLDocument]:
    """Round trip an SBML file through `sbml_to_model` and `create_model` at L3V2.

    The round trip is not validated: validation reports and never changes the document, and it is blind to the packages anyway.

    Args:
        sbml_path: path of the SBML file
        tmp_path: directory the round-tripped SBML is written to

    Returns:
        the document read and the document written; the caller has to hold both for as long as it uses any object of them, libsbml objects do not keep their document alive
    """
    doc_in: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(sbml_path))
    model = sbml_to_model(sbml_path)
    name = sbml_path.name.removesuffix(".gz").removesuffix(".xml")
    roundtrip_path = tmp_path / f"{name}-roundtrip.xml"
    create_model(
        model=model,
        filepath=roundtrip_path,
        sbml_level=3,
        sbml_version=2,
        validate=False,
    )
    doc_out: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(roundtrip_path))
    return doc_in, doc_out


# ---------------------------------------------------------------------------
# the snapshot
# ---------------------------------------------------------------------------
#: the metadata every element with its own compares
_METADATA: tuple[str, ...] = ("id", "name", "metaId", "sboTerm", "cvterms", "notes")

#: the attributes of a model, which a model definition compares
_MODEL_ATTRIBUTES: tuple[str, ...] = (
    "substanceUnits",
    "timeUnits",
    "volumeUnits",
    "areaUnits",
    "lengthUnits",
    "extentUnits",
    "conversionFactor",
)

#: the L3V2 core attributes of a core element of a model definition, by element
_CORE_ATTRIBUTES: dict[str, tuple[str, ...]] = {
    "functionDefinition": ("math",),
    "unitDefinition": (),
    "unit": ("kind", "exponent", "scale", "multiplier"),
    "compartment": ("spatialDimensions", "size", "units", "constant"),
    "species": (
        "compartment",
        "initialAmount",
        "initialConcentration",
        "substanceUnits",
        "hasOnlySubstanceUnits",
        "boundaryCondition",
        "constant",
        "conversionFactor",
    ),
    "parameter": ("value", "units", "constant"),
    "initialAssignment": ("symbol", "math"),
    "assignmentRule": ("variable", "math"),
    "rateRule": ("variable", "math"),
    "algebraicRule": ("math",),
    "constraint": ("math", "message"),
    "reaction": ("reversible", "fast", "compartment"),
    "speciesReference": ("species", "stoichiometry", "constant"),
    "modifierSpeciesReference": ("species",),
    "kineticLaw": ("math",),
    "localParameter": ("value", "units"),
    "event": ("useValuesFromTriggerTime",),
    "trigger": ("initialValue", "persistent", "math"),
    "priority": ("math",),
    "delay": ("math",),
    "eventAssignment": ("variable", "math"),
}

#: the references of an `SBaseRef`
_SBASEREF: tuple[str, ...] = ("portRef", "idRef", "unitRef", "metaIdRef")

#: the attributes of a package element, by construct
_PACKAGE_ATTRIBUTES: dict[str, tuple[str, ...]] = {
    "fbc.geneProduct": ("label", "associatedSpecies"),
    "fbc.objective": ("type",),
    "fbc.fluxObjective": ("reaction", "reaction2", "coefficient", "variableType"),
    "fbc.userDefinedConstraint": ("lowerBound", "upperBound"),
    "fbc.userDefinedConstraintComponent": (
        "coefficient",
        "variable",
        "variable2",
        "variableType",
    ),
    "fbc.keyValuePair": ("key", "value", "uri"),
    "distrib.uncertainty": (),
    "distrib.uncertParameter": (
        "type",
        "value",
        "var",
        "units",
        "definitionURL",
        "math",
    ),
    "comp.externalModelDefinition": ("source", "modelRef", "md5"),
    "comp.submodel": (
        "modelRef",
        "timeConversionFactor",
        "extentConversionFactor",
        "substanceConversionFactor",
    ),
    "comp.deletion": _SBASEREF,
    "comp.port": _SBASEREF,
    "comp.replacedElement": ("submodelRef", "deletion", "conversionFactor", *_SBASEREF),
    "comp.replacedBy": ("submodelRef", *_SBASEREF),
    "comp.sBaseRef": _SBASEREF,
}

#: the attributes an uncertSpan has in addition to an uncertParameter
_SPAN_ATTRIBUTES: tuple[str, ...] = ("valueLower", "varLower", "valueUpper", "varUpper")

#: the getters of the attributes which do not follow `isSet<Name>`/`get<Name>`
_GETTERS: dict[str, tuple[str, str]] = {
    # `getId` is the variable of a rule and the symbol of an initial assignment
    "id": ("isSetIdAttribute", "getIdAttribute"),
    "sboTerm": ("isSetSBOTerm", "getSBOTermID"),
    "notes": ("isSetNotes", "getNotesString"),
    "message": ("isSetMessage", "getMessageString"),
    # doubles, which the plain getter truncates to an integer
    "spatialDimensions": ("isSetSpatialDimensions", "getSpatialDimensionsAsDouble"),
    "exponent": ("isSetExponent", "getExponentAsDouble"),
    # enumerations, read as their name
    "variableType": ("isSetVariableType", "getVariableTypeAsString"),
}


def _qualifier(term: libsbml.CVTerm) -> str:
    """Name the qualifier of a CVTerm, e.g. `bqbiol:is`."""
    if term.getQualifierType() == libsbml.BIOLOGICAL_QUALIFIER:
        return "bqbiol:" + libsbml.BiolQualifierType_toString(
            term.getBiologicalQualifierType()
        )
    if term.getQualifierType() == libsbml.MODEL_QUALIFIER:
        return "bqmodel:" + libsbml.ModelQualifierType_toString(
            term.getModelQualifierType()
        )
    return f"unknown:{term.getQualifierType()}"


def _cvterms(element: libsbml.SBase) -> tuple[tuple[str, str], ...]:
    """Get the `(qualifier, resource)` pairs of the RDF annotation of an element."""
    pairs: set[tuple[str, str]] = set()
    for k in range(element.getNumCVTerms()):
        term: libsbml.CVTerm = element.getCVTerm(k)
        qualifier = _qualifier(term)
        for r in range(term.getNumResources()):
            pairs.add((qualifier, term.getResourceURI(r)))
    return tuple(sorted(pairs))


def _read(element: Any, attribute: str) -> object:
    """Read an attribute of a libsbml object.

    Args:
        element: the libsbml object, whose document is held
        attribute: the name of the attribute

    Returns:
        the value of the attribute, `None` if it is not set

    Raises:
        AttributeError: if the object has no getter for the attribute, which is a mistake of the comparison, never of the document
    """
    if attribute == "cvterms":
        return _cvterms(element)
    if attribute == "math":
        if not element.isSetMath():
            return None
        mathml: str = libsbml.writeMathMLToString(element.getMath())
        return mathml
    if attribute == "kind":
        return (
            libsbml.UnitKind_toString(element.getKind())
            if element.isSetKind()
            else None
        )
    capitalized = attribute[0].upper() + attribute[1:]
    is_set_name, get_name = _GETTERS.get(
        attribute, (f"isSet{capitalized}", f"get{capitalized}")
    )
    if attribute == "type" and hasattr(element, "getTypeAsString"):
        get_name = "getTypeAsString"
    is_set = getattr(element, is_set_name, None)
    if is_set is not None and not is_set():
        return None
    value: object = getattr(element, get_name)()
    return value


def _attributes(element: Any, attributes: Iterable[str]) -> Attributes:
    """Read the attributes and the metadata of an element."""
    return {name: _read(element, name) for name in (*attributes, *_METADATA)}


def _record(snap: Snapshot, construct: str, path: str, attributes: Attributes) -> None:
    """Record an element in a snapshot.

    Raises:
        AssertionError: if the snapshot has the key already, which is a mistake of the comparison
    """
    key = (construct, path)
    assert key not in snap, f"the comparison keyed two elements as {key}"
    snap[key] = attributes


#: how an element of a list is identified: a segment, or `None` for its position
_Key = Callable[[Any], str | None]


def _by_id(name: str) -> _Key:
    """Identify an element of a list by its id."""
    return lambda e: f"{name}:{e.getIdAttribute()}" if e.isSetIdAttribute() else None


def _by_reference(name: str, *attributes: str) -> _Key:
    """Identify an element of a list by the attributes it references."""

    def key(element: Any) -> str:
        values = [_read(element, attribute) for attribute in attributes]
        return f"{name}[{','.join(str(v) for v in values if v is not None)}]"

    return key


def _by_position(element: Any) -> None:
    """Identify an element of a list by its position."""
    return


def _items(
    path: str, items: Iterable[Any] | None, key: _Key, name: str | None = None
) -> Iterator[tuple[str, Any]]:
    """Key the elements of a list.

    Args:
        path: the path of the element which holds the list
        items: the elements of the list; libsbml creates some lists only when their first element is added, and returns `None` for one never created
        key: how an element is identified
        name: the name of the segment of an element identified by its position, its element name if `None`

    Yields:
        the path and the element, for every element of the list; a segment which repeats gets `#1`, `#2`, ... appended, an element identified by its position is `<name>#<position>` counted per name
    """
    repeated: Counter[str] = Counter()
    positions: Counter[str] = Counter()
    for item in items or ():
        segment = key(item)
        if segment is None:
            position_name = name or item.getElementName()
            segment = f"{position_name}#{positions[position_name]}"
            positions[position_name] += 1
        else:
            count = repeated[segment]
            repeated[segment] += 1
            if count:
                segment = f"{segment}#{count}"
        yield f"{path}/{segment}", item


def _replaced_key(element: Any) -> str:
    """Identify a replaced element by its submodel and what it references."""
    for attribute in ("portRef", "idRef", "unitRef", "metaIdRef", "deletion"):
        value = _read(element, attribute)
        if value is not None:
            return f"replacedElement[{element.getSubmodelRef()}/{attribute}={value}]"
    return f"replacedElement[{element.getSubmodelRef()}]"


def _deletion_key(element: Any) -> str:
    """Identify a deletion by its id, or by what it references."""
    if element.isSetIdAttribute():
        return f"deletion:{element.getIdAttribute()}"
    for attribute in _SBASEREF:
        value = _read(element, attribute)
        if value is not None:
            return f"deletion[{attribute}={value}]"
    return "deletion"


def _constraint_key(element: Any) -> str:
    """Identify a user-defined constraint by its id, or by its bounds."""
    if element.isSetIdAttribute():
        return f"userDefinedConstraint:{element.getIdAttribute()}"
    return f"userDefinedConstraint[{element.getLowerBound()},{element.getUpperBound()}]"


def _children(element: Any, path: str) -> Iterator[tuple[str, Any]]:
    """Yield every compared child of an element, with its path.

    Args:
        element: an element, whose document is held
        path: the path of the element

    Yields:
        the path and the child, for every core child, package child, and key-value pair, uncertainty, replaced element and replaced by of the element
    """
    name: str = element.getElementName()
    fbc = element.getPlugin("fbc")
    comp = element.getPlugin("comp")
    distrib = element.getPlugin("distrib")

    if name in ("model", "modelDefinition"):
        yield from _items(
            path, element.getListOfFunctionDefinitions(), _by_id("functionDefinition")
        )
        yield from _items(
            path, element.getListOfUnitDefinitions(), _by_id("unitDefinition")
        )
        yield from _items(path, element.getListOfCompartments(), _by_id("compartment"))
        yield from _items(path, element.getListOfSpecies(), _by_id("species"))
        yield from _items(path, element.getListOfParameters(), _by_id("parameter"))
        yield from _items(
            path,
            element.getListOfInitialAssignments(),
            _by_reference("initialAssignment", "symbol"),
        )
        yield from _items(
            path,
            element.getListOfRules(),
            lambda rule: (
                None
                if rule.getElementName() == "algebraicRule"
                else f"{rule.getElementName()}[{rule.getVariable()}]"
            ),
        )
        yield from _items(path, element.getListOfConstraints(), _by_position)
        yield from _items(path, element.getListOfReactions(), _by_id("reaction"))
        yield from _items(path, element.getListOfEvents(), _by_id("event"))
        if fbc is not None:
            yield from _items(path, fbc.getListOfGeneProducts(), _by_id("geneProduct"))
            yield from _items(path, fbc.getListOfObjectives(), _by_id("objective"))
            yield from _items(
                path, fbc.getListOfUserDefinedConstraints(), _constraint_key
            )
        if comp is not None:
            yield from _items(path, comp.getListOfSubmodels(), _by_id("submodel"))
            yield from _items(path, comp.getListOfPorts(), _by_id("port"))
    elif name == "unitDefinition":
        yield from _items(path, element.getListOfUnits(), _by_reference("unit", "kind"))
    elif name == "reaction":
        for role, species_references in [
            ("reactant", element.getListOfReactants()),
            ("product", element.getListOfProducts()),
            ("modifier", element.getListOfModifiers()),
        ]:
            yield from _items(
                path, species_references, _by_reference(role, "species"), name=role
            )
        if element.isSetKineticLaw():
            yield f"{path}/kineticLaw", element.getKineticLaw()
    elif name == "kineticLaw":
        yield from _items(
            path, element.getListOfLocalParameters(), _by_id("localParameter")
        )
    elif name == "event":
        for child in ("trigger", "priority", "delay"):
            capitalized = child.capitalize()
            if getattr(element, f"isSet{capitalized}")():
                yield f"{path}/{child}", getattr(element, f"get{capitalized}")()
        yield from _items(
            path,
            element.getListOfEventAssignments(),
            _by_reference("eventAssignment", "variable"),
        )
    elif name == "objective":
        yield from _items(
            path,
            element.getListOfFluxObjectives(),
            _by_reference("fluxObjective", "reaction", "reaction2"),
        )
    elif name == "userDefinedConstraint":
        yield from _items(
            path,
            element.getListOfUserDefinedConstraintComponents(),
            _by_reference("userDefinedConstraintComponent", "variable", "variable2"),
        )
    elif name == "submodel":
        yield from _items(path, element.getListOfDeletions(), _deletion_key)
    elif name in ("uncertainty", "uncertParameter", "uncertSpan"):
        yield from _items(
            path, element.getListOfUncertParameters(), _by_position, "uncertParameter"
        )

    chained = ("port", "deletion", "replacedElement", "replacedBy", "sBaseRef")
    if name in chained and element.isSetSBaseRef():
        yield f"{path}/sBaseRef", element.getSBaseRef()

    # the children every element can have
    if fbc is not None and hasattr(fbc, "getListOfKeyValuePairs"):
        yield from _items(
            path, fbc.getListOfKeyValuePairs(), _by_reference("keyValuePair", "key")
        )
    if distrib is not None and hasattr(distrib, "getListOfUncertainties"):
        yield from _items(path, distrib.getListOfUncertainties(), _by_position)
    if comp is not None and hasattr(comp, "getListOfReplacedElements"):
        yield from _items(path, comp.getListOfReplacedElements(), _replaced_key)
        if comp.isSetReplacedBy():
            yield f"{path}/replacedBy", comp.getReplacedBy()


def _association_nodes(node: Any) -> tuple[object, ...]:
    """Get the metadata of the nodes of an association which carry any.

    Args:
        node: the root of the association, whose document is held

    Returns:
        the element name, the gene product of a `geneProductRef` and the metadata of every node with metadata, in document order
    """
    nodes: list[object] = []
    stack = [node]
    while stack:
        current = stack.pop()
        metadata = tuple(_read(current, name) for name in _METADATA)
        if any(value not in (None, ()) for value in metadata):
            gene_product = (
                current.getGeneProduct() if current.isGeneProductRef() else ""
            )
            nodes.append((current.getElementName(), gene_product, metadata))
        if current.isFbcAnd() or current.isFbcOr():
            children = [
                current.getAssociation(k) for k in range(current.getNumAssociations())
            ]
            stack.extend(reversed(children))
    return tuple(nodes)


def _parameter_value(model: Any, sid: object) -> object:
    """Get the value of the parameter of an id, `None` if there is none."""
    if not isinstance(sid, str):
        return None
    parameter: libsbml.Parameter | None = model.getParameter(sid)
    if parameter is None or not parameter.isSetValue():
        return None
    value: float = parameter.getValue()
    return value


def _charge(fbc: libsbml.FbcSpeciesPlugin) -> float:
    """Get the charge of a species as libsbml writes it.

    libsbml keeps the integer charge of fbc v2 and the double charge of fbc v3 apart: it reads and writes only the one of the version of the document, and the getter of the other one returns 0.

    Args:
        fbc: the fbc plugin of a species with a charge, whose document is held

    Returns:
        the charge, as a float
    """
    if fbc.getPackageVersion() >= 3:
        return float(fbc.getChargeAsDouble())
    return float(fbc.getCharge())


def _record_core(
    snap: Snapshot, element: Any, path: str, model: Any, core: bool
) -> None:
    """Record a core element, and the package content it carries as attributes.

    Args:
        snap: the snapshot
        element: a core element, whose document is held
        path: the path of the element
        model: the model or model definition the element belongs to
        core: whether the core content itself is compared, in a model definition
    """
    name: str = element.getElementName()
    if core:
        _record(
            snap,
            f"comp.modelDefinition.{name}",
            path,
            _attributes(element, _CORE_ATTRIBUTES[name]),
        )

    fbc = element.getPlugin("fbc")
    if name == "species" and fbc is not None:
        if fbc.isSetCharge():
            _record(snap, "fbc.charge", path, {"charge": _charge(fbc)})
        if fbc.isSetChemicalFormula():
            _record(
                snap,
                "fbc.chemicalFormula",
                path,
                {"chemicalFormula": _read(fbc, "chemicalFormula")},
            )
    if name == "reaction" and fbc is not None:
        if fbc.isSetLowerFluxBound() or fbc.isSetUpperFluxBound():
            lower = _read(fbc, "lowerFluxBound")
            upper = _read(fbc, "upperFluxBound")
            _record(
                snap,
                "fbc.fluxBound",
                path,
                {
                    "lowerFluxBound": lower,
                    "upperFluxBound": upper,
                    "lowerValue": _parameter_value(model, lower),
                    "upperValue": _parameter_value(model, upper),
                },
            )
        if fbc.isSetGeneProductAssociation():
            gpa = fbc.getGeneProductAssociation()
            association = gpa.getAssociation() if gpa.isSetAssociation() else None
            _record(
                snap,
                "fbc.geneProductAssociation",
                path,
                {
                    "association": (
                        association.toInfix(True) if association is not None else None
                    ),
                    "nodes": (
                        _association_nodes(association)
                        if association is not None
                        else ()
                    ),
                    **_attributes(gpa, ()),
                },
            )

    if hasattr(element, "isSetMath"):
        mathml = _read(element, "math")
        if isinstance(mathml, str) and DISTRIB_CSYMBOL in mathml:
            _record(snap, "distrib.csymbol", path, {"math": mathml})


def _record_package(snap: Snapshot, element: Any, path: str, model: Any) -> None:
    """Record a package element.

    Args:
        snap: the snapshot
        element: an element of fbc, distrib or comp, whose document is held
        path: the path of the element
        model: the model or model definition the element belongs to
    """
    name: str = element.getElementName()
    if name == "uncertSpan":
        attributes = _attributes(
            element,
            (*_PACKAGE_ATTRIBUTES["distrib.uncertParameter"], *_SPAN_ATTRIBUTES),
        )
        _record(snap, "distrib.uncertParameter", path, {"element": name, **attributes})
        return

    construct = f"{element.getPackageName()}.{name}"
    attributes = _attributes(element, _PACKAGE_ATTRIBUTES[construct])
    if construct == "distrib.uncertParameter":
        attributes = {"element": name, **attributes}
    if construct == "fbc.objective":
        objectives: libsbml.ListOfObjectives = model.getPlugin(
            "fbc"
        ).getListOfObjectives()
        active = objectives.isSetActiveObjective() and (
            objectives.getActiveObjective() == element.getIdAttribute()
        )
        attributes = {"active": active, **attributes}
    _record(snap, construct, path, attributes)


def _visit(snap: Snapshot, element: Any, path: str, model: Any, core: bool) -> None:
    """Record an element and everything below it.

    Args:
        snap: the snapshot
        element: an element, whose document is held
        path: the path of the element
        model: the model or model definition the element belongs to
        core: whether core content is compared, in a model definition
    """
    if element.getPackageName() == "core":
        _record_core(snap, element, path, model, core)
    else:
        _record_package(snap, element, path, model)
    for child_path, child in _children(element, path):
        _visit(snap, child, child_path, model, core)


def _visit_model(
    snap: Snapshot, model: Any, path: str, core: bool, compare_strict: bool
) -> None:
    """Record the content of a model or of a model definition.

    Args:
        snap: the snapshot
        model: the model or model definition, whose document is held
        path: the path of the model
        core: whether core content is compared, in a model definition
        compare_strict: whether `fbc.strict` is recorded, see `snapshot`
    """
    fbc = model.getPlugin("fbc")
    if compare_strict and fbc is not None and fbc.isSetStrict():
        _record(snap, "fbc.strict", path, {"strict": fbc.getStrict()})
    for child_path, child in _children(model, path):
        _visit(snap, child, child_path, model, core)


def snapshot(doc: libsbml.SBMLDocument, compare_strict: bool = True) -> Snapshot:
    """Reduce the package content of a document to plain values, see the module docstring.

    The document has to be the one `comparable_document` returns: the walk reads the content of the versions the round trip writes, so the `fbc:fluxBound` elements of an fbc v1 document are never walked and a document of another level is compared against content it cannot have. Both are a mistake of the caller and are refused rather than reported as a missing construct.

    Args:
        doc: a document at L3V2 with fbc version 2 or higher, which the caller holds; `structural_diff` passes it through `comparable_document` first
        compare_strict: whether `fbc.strict` is part of the snapshot; `structural_diff` passes `False` for both documents of a round trip whose source declares fbc v1, whose `fbc:strict` is the invention of the converter, see the module docstring and `compares_fbc_strict`

    Returns:
        the attributes of every compared element, by `(construct, element id)`

    Raises:
        ValueError: if the document is not at L3V2, or if it declares fbc below version 2
    """
    if (doc.getLevel(), doc.getVersion()) != (3, 2):
        raise ValueError(
            f"a snapshot compares an L3V2 document, not L{doc.getLevel()}"
            f"V{doc.getVersion()}: pass it through comparable_document first"
        )
    fbc_plugin: libsbml.SBMLDocumentPlugin | None = doc.getPlugin("fbc")
    if fbc_plugin is not None and fbc_plugin.getPackageVersion() < 2:
        raise ValueError(
            f"a snapshot compares fbc version 2 or higher, not version "
            f"{fbc_plugin.getPackageVersion()}: pass the document through "
            f"comparable_document first"
        )

    snap: Snapshot = {}
    for package in PACKAGES:
        plugin: libsbml.SBMLDocumentPlugin | None = doc.getPlugin(package)
        if plugin is not None:
            _record(
                snap,
                f"{package}.package",
                "document",
                {
                    "version": plugin.getPackageVersion(),
                    "required": plugin.getRequired()
                    if plugin.isSetRequired()
                    else None,
                },
            )

    model: libsbml.Model | None = doc.getModel()
    if model is not None:
        _visit_model(snap, model, "model", core=False, compare_strict=compare_strict)

    comp: libsbml.CompSBMLDocumentPlugin | None = doc.getPlugin("comp")
    if comp is not None:
        for path, definition in _items(
            "",
            comp.getListOfExternalModelDefinitions(),
            _by_id("externalModelDefinition"),
        ):
            _visit(snap, definition, path.lstrip("/"), model, core=False)
        for path, definition in _items(
            "", comp.getListOfModelDefinitions(), _by_id("modelDefinition")
        ):
            path = path.lstrip("/")
            _record(
                snap,
                "comp.modelDefinition",
                path,
                _attributes(definition, _MODEL_ATTRIBUTES),
            )
            _visit_model(
                snap, definition, path, core=True, compare_strict=compare_strict
            )
    return snap


# ---------------------------------------------------------------------------
# the comparison
# ---------------------------------------------------------------------------
def _same(before: object, after: object) -> bool:
    """Test whether two values are equal, where two `NaN` are equal."""
    if before == after:
        return True
    return (
        isinstance(before, float)
        and isinstance(after, float)
        and math.isnan(before)
        and math.isnan(after)
    )


def _whitelisted(construct: str, attribute: str, before: object, after: object) -> bool:
    """Test whether a whitelist entry declares two values of an attribute the same.

    Args:
        construct: the construct of the element, e.g. `fbc.geneProductAssociation`
        attribute: the attribute which differs, e.g. `association`
        before: the value read
        after: the value written

    Returns:
        whether an entry of `WHITELIST` applies to this attribute of this construct and declares the two values the same
    """
    return any(
        entry.applies_to(construct, attribute) and entry.equivalent(before, after)
        for entry in WHITELIST
    )


def _frozen(attributes: Attributes) -> tuple[tuple[str, object], ...]:
    """Get the attributes of an element as a tuple, for a difference of the element."""
    return tuple(sorted(attributes.items(), key=lambda item: item[0]))


def diff_snapshots(before: Snapshot, after: Snapshot) -> list[Difference]:
    """Compare two snapshots, see the module docstring.

    Args:
        before: the snapshot of the document read
        after: the snapshot of the document written

    Returns:
        every difference which no whitelist entry declares the same, sorted by construct, element id and attribute
    """
    differences: list[Difference] = []
    for key in sorted(before.keys() | after.keys()):
        construct, element_id = key
        if key not in after:
            differences.append(
                Difference(construct, element_id, ELEMENT, _frozen(before[key]), ABSENT)
            )
            continue
        if key not in before:
            differences.append(
                Difference(construct, element_id, ELEMENT, ABSENT, _frozen(after[key]))
            )
            continue
        for attribute in sorted(before[key].keys() | after[key].keys()):
            value_before = before[key].get(attribute)
            value_after = after[key].get(attribute)
            if _same(value_before, value_after) or _whitelisted(
                construct, attribute, value_before, value_after
            ):
                continue
            differences.append(
                Difference(construct, element_id, attribute, value_before, value_after)
            )
    return differences


def snapshots(
    doc_in: libsbml.SBMLDocument, doc_out: libsbml.SBMLDocument
) -> tuple[Snapshot, Snapshot]:
    """Take the snapshot of both documents of a round trip, under the policy.

    This is the whole of the comparison policy which is not inside `snapshot` itself: both documents are brought to the versions the round trip writes, and both are snapshotted under the `compares_fbc_strict` of the **source**, see the module docstring. Every comparison goes through this, so that no caller has to remember it: `structural_diff`, the round-trip tests and `scripts/package_report.py`, which needs the two snapshots apart and therefore cannot call `structural_diff`.

    Args:
        doc_in: the document read, which the caller holds and which is not changed
        doc_out: the document written, which the caller holds and which is not changed

    Returns:
        the snapshot of the document read and the snapshot of the document written
    """
    compare_strict = compares_fbc_strict(doc_in)
    return (
        snapshot(comparable_document(doc_in), compare_strict=compare_strict),
        snapshot(comparable_document(doc_out), compare_strict=compare_strict),
    )


def structural_diff(
    doc_in: libsbml.SBMLDocument, doc_out: libsbml.SBMLDocument
) -> list[Difference]:
    """Compare the fbc, distrib and comp content of two documents, see the module docstring.

    Args:
        doc_in: the document read, which the caller holds and which is not changed
        doc_out: the document written, which the caller holds and which is not changed

    Returns:
        every difference in the package content, after applying `WHITELIST`
    """
    return diff_snapshots(*snapshots(doc_in, doc_out))
