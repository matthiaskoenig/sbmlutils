"""The analysis of an SBML model into its `OdeSystem`.

`analyse` reads the document (flattened, in L3) and `_Analysis` resolves the
semantics of SBML core which `sbmlutils.converters.ode.system` describes, one method
per element and rule.
"""

import re
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import libsbml

from sbmlutils.comp.flatten import flatten_sbml_doc
from sbmlutils.converters.ode.astutil import (
    drop_zero_terms,
    name,
    node,
    number,
    product,
    signed_sum,
    walk,
)
from sbmlutils.converters.ode.dependencies import names, order
from sbmlutils.converters.ode.events import trigger_root
from sbmlutils.converters.ode.system import (
    Assignment,
    Event,
    EventAssignment,
    FunctionDefinition,
    Kind,
    ModelInfo,
    Ode,
    OdeSystem,
    Participant,
    Quantity,
    Reaction,
    Role,
    Symbol,
)
from sbmlutils.io.sbml import read_sbml
from sbmlutils.report.units import udef_to_string

__all__ = ["analyse"]


def analyse(source: Path | str | libsbml.SBMLDocument) -> OdeSystem:
    """Analyse an SBML model into its ODE system, see `OdeSystem.from_sbml`."""
    doc, file_name, level = _document(source)
    return _Analysis(doc, file_name, level).system()


# --- reading --------------------------------------------------------------------------


def _document(
    source: Path | str | libsbml.SBMLDocument,
) -> tuple[libsbml.SBMLDocument, str | None, tuple[int, int]]:
    """The document of a source, flattened and in L3.

    A document which is passed is copied before it is changed.

    Returns:
        the document, the name of the file it was read from and the level and
        version it was written in
    """
    if isinstance(source, libsbml.SBMLDocument):
        doc, file_name, owned = source, None, False
    else:
        doc, owned = read_sbml(source), True
        is_sbml = isinstance(source, str) and "<sbml" in source
        file_name = None if is_sbml else Path(source).name
    model: libsbml.Model | None = doc.getModel()
    if model is None:
        raise ValueError("The SBML document has no model.")
    level = (doc.getLevel(), doc.getVersion())
    comp: libsbml.CompModelPlugin | None = model.getPlugin("comp")
    if comp is not None and comp.getNumSubmodels() > 0:
        doc = flatten_sbml_doc(doc if owned else doc.clone())
        owned = True
    if doc.getLevel() < 3:
        # L3 holds every construct of L1 and L2, a stoichiometry math becomes a
        # species reference with an assignment rule
        doc = doc if owned else doc.clone()
        if not doc.setLevelAndVersion(3, 2, False):
            raise ValueError(
                f"The L{level[0]}V{level[1]} document cannot be read as L3V2."
            )
    return doc, file_name, level


# the elements of XHTML which are blocks of text, a paragraph of the plain text each
_BLOCKS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "caption",
        "dd",
        "div",
        "dl",
        "dt",
        "figcaption",
        "figure",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tr",
        "ul",
    }
)
_CELLS = frozenset({"td", "th"})
# the edge of a text node, between which and an inline element the indentation of
# the XML adds white space, `(<em> x</em>\n )`
_EDGE = "\x00"
_AFTER_OPENING = re.compile(r"\(\s*\x00[\s\x00]*")
_BEFORE_PUNCTUATION = re.compile(r"[\s\x00]*\x00\s*([).,;:!?])")

# a unit without a magnitude, a product or a quotient, `l` or `m^3`
_SINGLE_UNIT = re.compile(r"[^\s*/()^]+(\^[0-9.]+)?")


def _plain_text(notes: libsbml.XMLNode) -> str:
    """The text of XHTML notes as paragraphs, separated by a blank line.

    A block of XHTML (`_BLOCKS`, e.g. a paragraph, a heading, an item of a list, a
    row of a table, a line break) is a paragraph, the cells of a row are separated
    by a space, and the white space of a paragraph is one space; the white space at
    the edge of an inline element after an opening parenthesis and before a closing
    one or a punctuation mark is none, so that the line breaks and the indentation
    of the XML do not show in the text.
    """
    paragraphs: list[str] = []
    texts: list[str] = []

    def flush() -> None:
        joined = "".join(texts)
        # the white space at the edge of an inline element, `( <i>x</i>\n )`, the
        # white space within a text, `a : b`, is kept
        joined = _AFTER_OPENING.sub("(", _BEFORE_PUNCTUATION.sub(r"\1", joined))
        paragraph = " ".join(joined.replace(_EDGE, "").split())
        if paragraph:
            paragraphs.append(paragraph)
        texts.clear()

    def visit(node: libsbml.XMLNode) -> None:
        if node.isText():
            texts.extend((_EDGE, node.getCharacters(), _EDGE))
            return
        block = node.getName() in _BLOCKS
        if block:
            flush()
        for k in range(node.getNumChildren()):
            visit(node.getChild(k))
        if block:
            flush()
        elif node.getName() in _CELLS:
            texts.append(" ")

    visit(notes)
    flush()
    return "\n\n".join(paragraphs)


def _rename(ast: libsbml.ASTNode, renamed: Mapping[str, str]) -> None:
    """Rename the names of the math in place."""
    for current in walk(ast):
        if current.getType() == libsbml.AST_NAME and current.getName() in renamed:
            current.setName(renamed[current.getName()])


# the types of the distrib functions, e.g. `normal(mean, sd)`
_DISTRIB = range(
    libsbml.AST_DISTRIB_FUNCTION_NORMAL, libsbml.AST_DISTRIB_FUNCTION_RAYLEIGH + 1
)


def _term(
    sign: int, stoichiometry: float | str, factor: str | None, rid: str
) -> tuple[int, libsbml.ASTNode]:
    """The signed term of a reaction in the ode of a species, `2 * f * J`.

    Args:
        sign: `-1` for a reactant, `1` for a product
        stoichiometry: the number or the id of the species reference
        factor: the conversion factor of the species
        rid: the id of the reaction

    Returns:
        the sign and the magnitude of the term, for `signed_sum`
    """
    factors = []
    if isinstance(stoichiometry, str):
        factors.append(name(stoichiometry))
    elif stoichiometry != 1.0:
        if stoichiometry < 0:
            sign, stoichiometry = -sign, -stoichiometry
        factors.append(number(stoichiometry))
    if factor:
        factors.append(name(factor))
    factors.append(name(rid))
    return sign, product(factors)


def _with_amounts(
    species: Sequence[Quantity], amounts: Sequence[Quantity]
) -> list[Quantity]:
    """The species, each followed by its amount if it is held as amount."""
    amount_of = {amount.amount_of: amount for amount in amounts}
    return [
        quantity
        for s in species
        for quantity in (s, amount_of.get(s.symbol.sid))
        if quantity is not None
    ]


def _ordered(assignments: list[Assignment]) -> tuple[Assignment, ...]:
    """The assignments in the order of their dependencies."""
    by_variable = {a.variable: a for a in assignments}
    items = [(a.variable, a.math) for a in assignments]
    return tuple(by_variable[sid] for sid in order(items))


# --- the analysis ---------------------------------------------------------------------


class _Analysis:
    """The analysis of one model, which builds its `OdeSystem`.

    The math of the document is read once into copies (`_math`), every math the
    system holds is a copy with each rateOf resolved (`_resolve`).
    """

    def __init__(
        self, doc: libsbml.SBMLDocument, file_name: str | None, level: tuple[int, int]
    ) -> None:
        """Read the rules of the model and the ids it takes.

        Args:
            doc: the document, flattened and in L3
            file_name: the name of the file the document was read from
            level: the level and version the document was written in
        """
        # the document owns the model, it is kept alive while the model is read
        self.doc = doc
        self.model: libsbml.Model = doc.getModel()
        self.file_name = file_name
        self.level = level
        self.unsupported: list[tuple[str, str]] = []
        self.taken: set[str] = {
            element.getIdAttribute() for element in self.model.getListOfAllElements()
        } | {self.model.getId()}
        self.rate_rules: dict[str, libsbml.ASTNode] = {}
        self.assignment_rules: dict[str, libsbml.ASTNode] = {}
        self.initial_assignments: dict[str, libsbml.ASTNode] = {}
        self.event_variables: set[str] = {
            assignment.getVariable()
            for event in self.model.getListOfEvents()
            for assignment in event.getListOfEventAssignments()
        }
        self._read_rules()
        # the quantities and reactions by id, the amount of each species held as
        # amount, the conversion factor of each species, the right hand side of
        # each state as read and with its rateOf resolved
        self.quantities: dict[str, Quantity] = {}
        self.reaction_ids: set[str] = set()
        self.amounts: dict[str, str] = {}
        self.factors: dict[str, str] = {}
        self.rhs: dict[str, libsbml.ASTNode] = {}
        self.resolved: dict[str, libsbml.ASTNode] = {}

    # --- helpers ------------------------------------------------------------------

    def _unique(self, base: str) -> str:
        """An id which the model does not take, `base`, else `base_1`, `base_2`, ..."""
        sid, k = base, 0
        while sid in self.taken:
            k += 1
            sid = f"{base}_{k}"
        self.taken.add(sid)
        return sid

    def _unit(self, uid: str) -> str | None:
        """The unit of a unit id, `None` if it is not set."""
        return udef_to_string(uid, model=self.model, format="str") if uid else None

    def _symbol(
        self, element: libsbml.SBase, kind: Kind, unit: str | None, sid: str = ""
    ) -> Symbol:
        """The symbol of an element, under the given id if it is renamed."""
        return Symbol(
            sid=sid or element.getId(),
            name=element.getName() if element.isSetName() else None,
            unit=unit,
            sbo=element.getSBOTermID() if element.isSetSBOTerm() else None,
            kind=kind,
        )

    def _math(self, element: str, ast: libsbml.ASTNode) -> libsbml.ASTNode:
        """A copy of the math of an element, its unsupported constructs collected."""
        for current in walk(ast):
            if current.getType() == libsbml.AST_FUNCTION_DELAY:
                self._unsupported("delay", element)
            elif current.getType() in _DISTRIB:
                self._unsupported("distrib function", element)
        return ast.deepCopy()

    def _unsupported(self, construct: str, element: str) -> None:
        """Collect an unsupported construct once."""
        if (construct, element) not in self.unsupported:
            self.unsupported.append((construct, element))

    def _read_rules(self) -> None:
        """Read the rules and the initial assignments by their variable."""
        rule: libsbml.Rule
        for k, rule in enumerate(self.model.getListOfRules()):
            if rule.isAlgebraic():
                label = rule.getIdAttribute() or rule.getMetaId() or f"rule{k}"
                self._unsupported("algebraic rule", label)
                continue
            variable = rule.getVariable()
            if variable in self.rate_rules or variable in self.assignment_rules:
                raise ValueError(f"The variable '{variable}' has more than one rule.")
            # a rule without math is ignored (L3V2)
            if rule.isSetMath():
                rules = self.rate_rules if rule.isRate() else self.assignment_rules
                rules[variable] = self._math(variable, rule.getMath())
        assignment: libsbml.InitialAssignment
        for assignment in self.model.getListOfInitialAssignments():
            symbol = assignment.getSymbol()
            if symbol in self.assignment_rules or symbol in self.initial_assignments:
                raise ValueError(
                    f"The variable '{symbol}' has an initial assignment and an "
                    f"assignment rule or a second initial assignment."
                )
            # an initial assignment without math is ignored (L3V2)
            if assignment.isSetMath():
                math = self._math(symbol, assignment.getMath())
                self.initial_assignments[symbol] = math

    def _role(self, sid: str) -> Role:
        """The role of a quantity by its rules."""
        if sid in self.rate_rules:
            return "state"
        return "assigned" if sid in self.assignment_rules else "constant"

    def _quantity(
        self,
        element: libsbml.Compartment | libsbml.Parameter | libsbml.SpeciesReference,
        kind: Kind,
        unit: str | None,
        value: float | None,
    ) -> Quantity:
        """The quantity of a compartment, parameter or species reference."""
        return Quantity(
            symbol=self._symbol(element, kind, unit),
            value=value,
            constant=element.getConstant(),
            role=self._role(element.getId()),
        )

    # --- the system ---------------------------------------------------------------

    def system(self) -> OdeSystem:
        """Analyse the model into its ODE system."""
        functions = self._read_functions()
        reactions, local_parameters, references = self._read_reactions()
        compartments = [
            self._quantity(
                c,
                "compartment",
                self._compartment_unit(c),
                # a compartment without a size has the size 1, as roadrunner holds
                # it, e.g. a compartment of 0 dimensions
                c.getSize() if c.isSetSize() else 1.0,
            )
            for c in self.model.getListOfCompartments()
        ]
        species, amounts = self._read_species(reactions)
        parameters = [
            self._quantity(
                p,
                "parameter",
                self._unit(p.getUnits()),
                p.getValue() if p.isSetValue() else None,
            )
            for p in self.model.getListOfParameters()
        ]
        parameters.extend(local_parameters)
        quantities = [
            *compartments,
            *_with_amounts(species, amounts),
            *parameters,
            *references,
        ]
        self.quantities = {q.symbol.sid: q for q in quantities}
        self.reaction_ids = {r.symbol.sid for r in reactions}
        odes = self._build_odes(quantities, reactions)
        odes = [
            replace(ode, rhs=self._resolved_rate(ode.variable, ode.variable))
            for ode in odes
        ]
        reactions = [
            replace(r, rate=self._resolve(r.rate, r.symbol.sid)) for r in reactions
        ]
        return OdeSystem(
            info=self._read_info(),
            compartments=tuple(compartments),
            species=tuple(species),
            amounts=tuple(amounts),
            parameters=tuple(parameters),
            species_references=tuple(references),
            functions=tuple(functions),
            assignments=self._build_assignments(amounts, reactions),
            initial=self._build_initial(quantities, reactions),
            reactions=tuple(reactions),
            odes=tuple(odes),
            events=tuple(self._read_events()),
            unsupported=tuple(self.unsupported),
        )

    # --- the elements -------------------------------------------------------------

    def _read_info(self) -> ModelInfo:
        """The information of the model."""
        model = self.model
        units = {
            "time": model.getTimeUnits(),
            "substance": model.getSubstanceUnits(),
            "extent": model.getExtentUnits(),
            "volume": model.getVolumeUnits(),
            "area": model.getAreaUnits(),
            "length": model.getLengthUnits(),
        }
        return ModelInfo(
            sid=model.getId() if model.isSetId() else None,
            name=model.getName() if model.isSetName() else None,
            level=self.level[0],
            version=self.level[1],
            notes=_plain_text(model.getNotes()) if model.isSetNotes() else None,
            units={key: self._unit(uid) for key, uid in units.items()},
            source=self.file_name,
        )

    def _read_functions(self) -> list[FunctionDefinition]:
        """The function definitions, which stay functions called by the math."""
        functions = []
        function: libsbml.FunctionDefinition
        for function in self.model.getListOfFunctionDefinitions():
            fid = function.getId()
            body: libsbml.ASTNode | None = function.getBody()
            # a function definition without math is ignored (L3V2)
            if body is None:
                continue
            body = self._math(fid, body)
            if any(n.getType() == libsbml.AST_FUNCTION_RATE_OF for n in walk(body)):
                self._unsupported("rateOf in a function definition", fid)
            arguments = tuple(
                function.getArgument(k).getName()
                for k in range(function.getNumArguments())
            )
            symbol = self._symbol(function, "function", None)
            functions.append(FunctionDefinition(symbol, arguments, body))
        return functions

    def _read_reactions(self) -> tuple[list[Reaction], list[Quantity], list[Quantity]]:
        """The reactions, their renamed local parameters and species references."""
        extent = self._unit(self.model.getExtentUnits())
        time = self._unit(self.model.getTimeUnits())
        unit = f"{extent}/{time}" if extent and time else None
        reactions: list[Reaction] = []
        local_parameters: list[Quantity] = []
        references: list[Quantity] = []
        reaction: libsbml.Reaction
        for reaction in self.model.getListOfReactions():
            rid = reaction.getId()
            if reaction.isSetFast() and reaction.getFast():
                self._unsupported("fast reaction", rid)
            law: libsbml.KineticLaw | None = reaction.getKineticLaw()
            renamed: dict[str, str] = {}
            parameter: libsbml.LocalParameter
            for parameter in [] if law is None else law.getListOfLocalParameters():
                sid = self._unique(f"{rid}_{parameter.getId()}")
                renamed[parameter.getId()] = sid
                symbol = self._symbol(
                    parameter, "parameter", self._unit(parameter.getUnits()), sid
                )
                value = parameter.getValue() if parameter.isSetValue() else None
                local_parameters.append(Quantity(symbol, value, True, "constant"))
            if law is not None and law.isSetMath():
                rate = self._math(rid, law.getMath())
                _rename(rate, renamed)
            else:
                # a reaction without a kinetic law has no flux, as roadrunner holds it
                rate = number(0.0)
            sides: list[list[Participant]] = [[], []]
            for side, listed in enumerate(
                (reaction.getListOfReactants(), reaction.getListOfProducts())
            ):
                ref: libsbml.SpeciesReference
                for ref in listed:
                    sides[side].append(self._participant(ref))
                    if ref.isSetId():
                        # an unset stoichiometry is 1, as roadrunner holds it
                        value = (
                            ref.getStoichiometry() if ref.isSetStoichiometry() else 1.0
                        )
                        references.append(
                            self._quantity(ref, "species_reference", None, value)
                        )
            reactions.append(
                Reaction(
                    symbol=self._symbol(reaction, "reaction", unit),
                    reactants=tuple(sides[0]),
                    products=tuple(sides[1]),
                    modifiers=tuple(
                        m.getSpecies() for m in reaction.getListOfModifiers()
                    ),
                    reversible=reaction.getReversible(),
                    rate=rate,
                    local_parameters=tuple(renamed.values()),
                )
            )
        return reactions, local_parameters, references

    def _participant(self, ref: libsbml.SpeciesReference) -> Participant:
        """The species of a species reference and its stoichiometry."""
        sid = ref.getId()
        changed = (
            self.rate_rules,
            self.assignment_rules,
            self.initial_assignments,
            self.event_variables,
        )
        if ref.isSetId() and any(sid in ids for ids in changed):
            return Participant(ref.getSpecies(), sid)
        value = ref.getStoichiometry() if ref.isSetStoichiometry() else 1.0
        return Participant(ref.getSpecies(), value)

    def _compartment_unit(self, compartment: libsbml.Compartment) -> str | None:
        """The unit of a compartment, else the unit of the model of its dimensions."""
        if compartment.isSetUnits():
            return self._unit(compartment.getUnits())
        default = {
            3.0: self.model.getVolumeUnits,
            2.0: self.model.getAreaUnits,
            1.0: self.model.getLengthUnits,
        }.get(compartment.getSpatialDimensionsAsDouble())
        return self._unit(default()) if default else None

    def _species_unit(self, species: libsbml.Species) -> tuple[str | None, str | None]:
        """The unit of the substance of a species and the unit of the species."""
        substance = self._unit(
            species.getSubstanceUnits() or self.model.getSubstanceUnits()
        )
        if species.getHasOnlySubstanceUnits():
            return substance, substance
        compartment = self.model.getCompartment(species.getCompartment())
        volume = self._compartment_unit(compartment) if compartment else None
        if not substance or not volume:
            return substance, None
        # a single unit, also with an exponent, needs no parentheses, mmol/m^3
        single = _SINGLE_UNIT.fullmatch(volume) is not None
        return substance, f"{substance}/{volume if single else f'({volume})'}"

    def _read_species(
        self, reactions: list[Reaction]
    ) -> tuple[list[Quantity], list[Quantity]]:
        """The species and the amounts of the species held as amount."""
        reacting = {p.species for r in reactions for p in (*r.reactants, *r.products)}
        species_list: list[Quantity] = []
        amounts: list[Quantity] = []
        species: libsbml.Species
        for species in self.model.getListOfSpecies():
            sid, cid = species.getId(), species.getCompartment()
            in_amount = species.getHasOnlySubstanceUnits()
            boundary, constant = species.getBoundaryCondition(), species.getConstant()
            substance, unit = self._species_unit(species)
            factor = species.getConversionFactor() or self.model.getConversionFactor()
            if factor:
                self.factors[sid] = factor
            value = None
            if species.isSetInitialAmount() and in_amount:
                value = species.getInitialAmount()
            elif species.isSetInitialConcentration() and not in_amount:
                value = species.getInitialConcentration()
            role: Role = (
                "state"
                if sid in reacting and not boundary and not constant
                else "constant"
            )
            variable_size = self._role(cid) != "constant" or cid in self.event_variables
            if sid in self.assignment_rules or sid in self.rate_rules:
                role = self._role(sid)
            elif not in_amount and variable_size:
                # held as amount, the concentration is assigned
                aid = self._unique(f"n_{sid}")
                self.amounts[sid] = aid
                amounts.append(
                    Quantity(
                        symbol=Symbol(
                            aid,
                            f"amount of {species.getName() or sid}",
                            substance,
                            None,
                            "species",
                        ),
                        value=(
                            species.getInitialAmount()
                            if species.isSetInitialAmount()
                            else None
                        ),
                        constant=constant,
                        role=role,
                        compartment=cid,
                        amount=True,
                        boundary=boundary,
                        conversion_factor=factor or None,
                        amount_of=sid,
                    )
                )
                role = "assigned"
            species_list.append(
                Quantity(
                    symbol=self._symbol(species, "species", unit),
                    value=value,
                    constant=constant,
                    role=role,
                    compartment=cid,
                    amount=in_amount,
                    boundary=boundary,
                    conversion_factor=factor or None,
                )
            )
        return species_list, amounts

    # --- the odes -----------------------------------------------------------------

    def _build_odes(
        self, quantities: list[Quantity], reactions: list[Reaction]
    ) -> list[Ode]:
        """The odes of the states, their right hand sides with rateOf not resolved."""
        terms: dict[str, list[tuple[int, libsbml.ASTNode]]] = {}
        for reaction in reactions:
            rid = reaction.symbol.sid
            for sign, side in ((-1, reaction.reactants), (1, reaction.products)):
                for p in side:
                    term = _term(
                        sign, p.stoichiometry, self.factors.get(p.species), rid
                    )
                    terms.setdefault(p.species, []).append(term)
        odes = []
        for quantity in quantities:
            sid = quantity.symbol.sid
            if quantity.role != "state":
                continue
            if sid in self.rate_rules:
                ode = Ode(sid, self.rate_rules[sid], "rate_rule")
            elif quantity.amount:
                reaction_terms = signed_sum(terms[quantity.amount_of or sid])
                rhs = reaction_terms.deepCopy()
                ode = Ode(
                    sid, rhs, "reactions", reaction_terms, None, quantity.amount_of
                )
            else:
                reaction_terms = signed_sum(terms[sid])
                cid = str(quantity.compartment)
                rhs = node(libsbml.AST_DIVIDE, reaction_terms.deepCopy(), name(cid))
                ode = Ode(sid, rhs, "reactions", reaction_terms, cid)
            self.rhs[sid] = ode.rhs
            odes.append(ode)
        return odes

    def _resolved_rate(
        self, sid: str, element: str, stack: frozenset[str] = frozenset()
    ) -> libsbml.ASTNode:
        """A copy of the right hand side of a state with every rateOf resolved."""
        if sid not in self.resolved:
            if sid in stack:
                raise ValueError(
                    f"The rates of {sorted(stack)} depend on each other in a cycle."
                )
            self.resolved[sid] = self._resolve(self.rhs[sid], element, stack | {sid})
        return self.resolved[sid].deepCopy()

    def _rate_of(
        self, sid: str, element: str, stack: frozenset[str]
    ) -> libsbml.ASTNode | None:
        """The rate of change of an id, `None` if it is unsupported."""
        if sid in self.rhs:
            return self._resolved_rate(sid, element, stack)
        if sid in self.amounts:
            # the concentration of an amount: d(n/V)/dt = (dn/dt - S dV/dt) / V
            aid, cid = self.amounts[sid], str(self.quantities[sid].compartment)
            if cid in self.assignment_rules:
                self._unsupported("rateOf of an assigned variable", element)
                return None
            rate = self._resolved_rate(aid, element, stack) if aid in self.rhs else None
            if cid in self.rhs:
                size_rate = self._resolved_rate(cid, element, stack)
                dilution = node(libsbml.AST_TIMES, name(sid), size_rate)
                rate = signed_sum(
                    [*([] if rate is None else [(1, rate)]), (-1, dilution)]
                )
            if rate is None:
                return number(0.0)
            return node(libsbml.AST_DIVIDE, rate, name(cid))
        quantity = self.quantities.get(sid)
        if quantity is None and sid not in self.reaction_ids:
            raise ValueError(
                f"The rateOf in '{element}' refers to the unknown id '{sid}'."
            )
        if quantity is not None and quantity.role == "constant":
            return number(0.0)
        self._unsupported("rateOf of an assigned variable", element)
        return None

    def _resolve(
        self, ast: libsbml.ASTNode, element: str, stack: frozenset[str] = frozenset()
    ) -> libsbml.ASTNode:
        """A copy of the math with every supported rateOf replaced by the rate.

        The terms which become 0, the rate of a constant, are dropped.
        """
        copy = ast.deepCopy()
        if copy.getType() == libsbml.AST_FUNCTION_RATE_OF:
            return self._replacement(copy, element, stack) or copy
        replaced = False
        parents = [copy]
        while parents:
            parent = parents.pop()
            for k in range(parent.getNumChildren()):
                child = parent.getChild(k)
                rate = None
                if child.getType() == libsbml.AST_FUNCTION_RATE_OF:
                    rate = self._replacement(child, element, stack)
                if rate is None:
                    parents.append(child)
                else:
                    # the parent takes ownership of the rate and deletes the rateOf
                    parent.replaceChild(k, rate, True)
                    replaced = True
        return drop_zero_terms(copy) if replaced else copy

    def _replacement(
        self, rate_of: libsbml.ASTNode, element: str, stack: frozenset[str]
    ) -> libsbml.ASTNode | None:
        """The rate of change of the argument of a rateOf, `None` if unsupported."""
        argument = rate_of.getChild(0) if rate_of.getNumChildren() == 1 else None
        if argument is None or argument.getType() != libsbml.AST_NAME:
            self._unsupported("rateOf of an expression", element)
            return None
        return self._rate_of(argument.getName(), element, stack)

    # --- assignments and initial values -------------------------------------------

    def _build_assignments(
        self, amounts: list[Quantity], reactions: list[Reaction]
    ) -> tuple[Assignment, ...]:
        """The concentrations, assignment rules and reaction rates in dependency order."""
        assignments = [
            Assignment(str(q.amount_of), self._concentration(q), "concentration")
            for q in amounts
        ]
        assignments.extend(
            Assignment(sid, self._resolve(ast, sid), "assignment_rule")
            for sid, ast in self.assignment_rules.items()
        )
        assignments.extend(
            Assignment(r.symbol.sid, r.rate.deepCopy(), "reaction") for r in reactions
        )
        return _ordered(assignments)

    @staticmethod
    def _concentration(amount: Quantity) -> libsbml.ASTNode:
        """The concentration of the species of an amount, `n / V`."""
        cid = str(amount.compartment)
        return node(libsbml.AST_DIVIDE, name(amount.symbol.sid), name(cid))

    def _initial_of(self, quantity: Quantity) -> Assignment | None:
        """The initial value of a quantity if it is computed at t=0."""
        sid, cid = quantity.symbol.sid, str(quantity.compartment)
        if sid in self.assignment_rules:
            math = self._resolve(self.assignment_rules[sid], sid)
            return Assignment(sid, math, "assignment_rule")
        if sid in self.initial_assignments:
            math = self._resolve(self.initial_assignments[sid], sid)
            return Assignment(sid, math, "initial_assignment")
        species: libsbml.Species | None = self.model.getSpecies(sid)
        if quantity.amount_of is not None:
            # the initial amount, else the amount of the initial concentration
            if quantity.value is None or quantity.amount_of in self.initial_assignments:
                math = node(libsbml.AST_TIMES, name(quantity.amount_of), name(cid))
                return Assignment(sid, math, "initial_value")
        elif sid in self.amounts:
            if species is not None and species.isSetInitialAmount():
                return Assignment(
                    sid,
                    self._concentration(self.quantities[self.amounts[sid]]),
                    "concentration",
                )
            return Assignment(sid, number(quantity.value), "initial_value")
        elif species is not None:
            # converted with the initial size of the compartment
            if species.isSetInitialAmount() and not quantity.amount:
                value = number(species.getInitialAmount())
                math = node(libsbml.AST_DIVIDE, value, name(cid))
                return Assignment(sid, math, "initial_value")
            if species.isSetInitialConcentration() and quantity.amount:
                value = number(species.getInitialConcentration())
                math = node(libsbml.AST_TIMES, value, name(cid))
                return Assignment(sid, math, "initial_value")
        if quantity.role == "state":
            return Assignment(sid, number(quantity.value), "initial_value")
        return None

    def _build_initial(
        self, quantities: list[Quantity], reactions: list[Reaction]
    ) -> tuple[Assignment, ...]:
        """The initial values at t=0 in dependency order, with the rates they need."""
        initial = [a for q in quantities if (a := self._initial_of(q)) is not None]
        referenced = set().union(*(names(a.math) for a in initial))
        needed: set[str] = set()
        while True:
            # the rates the initial values need, and the rates these need
            new = [r for r in reactions if r.symbol.sid in referenced - needed]
            if not new:
                break
            for reaction in new:
                needed.add(reaction.symbol.sid)
                referenced |= names(reaction.rate)
        initial.extend(
            Assignment(r.symbol.sid, r.rate.deepCopy(), "reaction")
            for r in reactions
            if r.symbol.sid in needed
        )
        return _ordered(initial)

    # --- events -------------------------------------------------------------------

    def _read_events(self) -> list[Event]:
        """The events, their assignments to the representation of the states."""
        events = []
        event: libsbml.Event
        for k, event in enumerate(self.model.getListOfEvents()):
            eid = event.getId() if event.isSetId() else self._unique(f"event{k}")
            trigger_element: libsbml.Trigger | None = event.getTrigger()
            if trigger_element is not None and trigger_element.isSetMath():
                trigger = self._resolve(self._math(eid, trigger_element.getMath()), eid)
            else:
                # an event without a trigger never fires (L3V2)
                trigger = libsbml.ASTNode(libsbml.AST_CONSTANT_FALSE)
            # the root of a call of a function definition is the root of its body
            expanded = trigger.deepCopy()
            libsbml.SBMLTransforms.replaceFD(
                expanded, self.model.getListOfFunctionDefinitions()
            )
            try:
                root: libsbml.ASTNode | None = trigger_root(expanded)
            except NotImplementedError:
                self._unsupported("event trigger", eid)
                root = None
            events.append(
                Event(
                    symbol=self._symbol(event, "event", None, eid),
                    trigger=trigger,
                    root=root,
                    initial_value=(
                        trigger_element is None or trigger_element.getInitialValue()
                    ),
                    persistent=(
                        trigger_element is None or trigger_element.getPersistent()
                    ),
                    delay=self._optional_math(eid, event.getDelay()),
                    priority=self._optional_math(eid, event.getPriority()),
                    use_values_from_trigger_time=event.getUseValuesFromTriggerTime(),
                    assignments=self._event_assignments(eid, event),
                )
            )
        return events

    def _optional_math(
        self, element: str, sbase: libsbml.Delay | libsbml.Priority | None
    ) -> libsbml.ASTNode | None:
        """The math of a delay or a priority, `None` if it is not set."""
        if sbase is None or not sbase.isSetMath():
            return None
        return self._resolve(self._math(element, sbase.getMath()), element)

    def _event_assignments(
        self, eid: str, event: libsbml.Event
    ) -> tuple[EventAssignment, ...]:
        """The assignments of an event to the states and constants of the system.

        The concentration of a species held as amount is assigned as amount, its
        value scaled by the size at the execution (test case 01779). A species in
        concentration with a rate rule is rescaled when the event changes the size
        of its compartment, its amount stays (test case 01506). See
        `EventAssignment` for when each part is evaluated.
        """
        assigned: dict[str, libsbml.ASTNode] = {}
        assignment: libsbml.EventAssignment
        for assignment in event.getListOfEventAssignments():
            variable = assignment.getVariable()
            quantity = self.quantities.get(variable)
            if quantity is None:
                raise ValueError(
                    f"The event '{eid}' assigns '{variable}', which is no quantity."
                )
            if not assignment.isSetMath():
                continue
            if quantity.constant:
                self._unsupported("event assignment to a constant", eid)
            elif quantity.role == "assigned" and variable not in self.amounts:
                self._unsupported("event assignment to an assigned variable", eid)
            else:
                math = self._math(eid, assignment.getMath())
                assigned[variable] = self._resolve(math, eid)
        result = []
        for variable, math in assigned.items():
            cid = str(self.quantities[variable].compartment)
            if variable in self.amounts:
                amount = self.amounts[variable]
                result.append(EventAssignment(amount, math, scale=name(cid)))
            elif self._rescaled(variable) and cid in assigned:
                result.append(EventAssignment(variable, math, name(cid), cid))
            else:
                result.append(EventAssignment(variable, math))
        for sid, quantity in self.quantities.items():
            cid = str(quantity.compartment)
            if self._rescaled(sid) and cid in assigned and sid not in assigned:
                scale = node(libsbml.AST_TIMES, name(sid), name(cid))
                result.append(EventAssignment(sid, None, scale, cid))
        return tuple(result)

    def _rescaled(self, sid: str) -> bool:
        """Check that an id is a species in concentration with a rate rule."""
        quantity = self.quantities[sid]
        return (
            quantity.symbol.kind == "species"
            and sid in self.rate_rules
            and not quantity.amount
        )
