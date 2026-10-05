r"""The context of the document formats of the ODE export: typst, LaTeX and markdown.

A document describes the model to a reader in the sections of the specification:
title and metadata, units, compartments, species, parameters, function definitions,
initial assignments and assignment rules, reactions, the ODE system, events and the
unsupported constructs. `DocumentContext.build` gives a template every text and every
math of these as markup of its format, so that a template only lays them out:

- text (names, notes, units, flags) is escaped for the markup of the format with
  `text.typst_text`, `text.tex_text` or `text.markdown_text`, a unit additionally
  with its exponents as superscripts and its products as `·`, `mol·m³`, and
  without ligatures, `fl` is two letters;
- an id is code, `` `k1` `` in typst and markdown, `\texttt{k1}` in LaTeX, and is
  checked to be an SId (`ValueError` otherwise, libsbml reads a document with any
  id, which could end the code and write markup; an unsupported element without an
  id is labelled by its metaid, an XML ID); an id of more than `LONG_ID` characters
  may break after an underscore in typst and LaTeX (`#sym.zws`, `\allowbreak`),
  which writes no character, so that a table with long ids fits the page;
- math is printed with the printer of the format, `LatexPrinter` for LaTeX and
  markdown (in `$$ ... $$`), `TypstPrinter` for typst, the ids written as the math
  symbols of `symbols.typeset_names` (`symbols="id"` or `"name"`): the rate of a
  reaction is `v` with the id as subscript, `v_{\mathrm{J0}}`, the amount of a
  species held as amount is `n` with the symbol of the species as subscript,
  `n_{S}`;
- a long sum is a list of lines (`DocumentPrinter.print_lines`), which a template
  joins into the lines of an alignment; a line after the first begins with its sign.

The context holds:

- `model`: `title` (the name, else the id), `plain_title` (the title without the
  opportunities of line breaks and without math, `text.tex_pdf_text`, for the
  bookmarks of a PDF), `id`, `level`, `version`, `source`, `sbmlutils` (the version
  which writes the document) and `notes`, the paragraphs of the notes;
- `units`: the units of the model, each with `kind` and `unit`;
- `compartments`, `parameters`: rows with `symbol`, `id`, `long_id` (whether the id
  is longer than `LONG_ID`, a template lets its column wrap), `name`, `value`
  (math, empty for a value given by a rule or a conversion), `unit` and
  `constant`; the parameters include the local parameters and the species
  references with an id; `species` additionally `compartment` (math, `None` for a
  species in amount without a compartment) and `properties` (amount or
  concentration, boundary and constant as text);
- `functions`: `lhs` (`f(x, y)`) and `rhs`;
- `initial`: the initial assignments and the initial values which are a conversion
  between amount and concentration, `assignments`: the assignment rules and the
  concentrations of the species held as amount, each with `lhs`, `lines` and
  `origin`;
- `amounts`: the species held as amount, with `amount`, `species` and
  `compartment` as math;
- `reactions`: `symbol` (`v_{J0}`), `id`, `long_id`, `name`, `equation` (math,
  `2 A + B ⟶ C`, `⇌` if reversible, `∅` for no species), `modifiers` and
  `local_parameters` (math, comma separated), `lines` of the rate;
- `odes`: `lhs` (`dS/dt`), `lines` and `origin`, the right hand side written with
  the rates of the reactions and divided by the volume of a species in
  concentration (`(v_1 - v_2)/V`, in lines `1/V (v_1 - v_2 ...)`), or the rate
  rule;
- `events`: `id`, `name`, `trigger`, `delay`, `priority` (math, `None` without),
  `initial_value`, `persistent`, `use_trigger_values` and `assignments` with `lhs`
  and `rhs`, the effective value with the conversion of a size, `conversion`
  (`None`, `amount` for the amount of a `species` in concentration, `resized` for a
  concentration whose `compartment` the event resizes to `new`, `V^{new}`);
- `unsupported`: `construct` and `id`;
- `options`: the options of the rendering.

The headings, labels and sentences of a document are written by its template.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import libsbml

import sbmlutils
from sbmlutils.converters.ode.astutil import is_number, name, node, product
from sbmlutils.converters.ode.printers import (
    DocumentPrinter,
    LatexPrinter,
    Precedence,
    Printed,
    TypstPrinter,
)
from sbmlutils.converters.ode.symbols import typeset_names, typeset_symbol
from sbmlutils.converters.ode.text import (
    check_sid,
    markdown_text,
    tex_pdf_text,
    tex_text,
    typst_text,
)

if TYPE_CHECKING:
    from sbmlutils.converters.ode.system import (
        EventAssignment,
        Ode,
        OdeSystem,
        Participant,
        Quantity,
    )

__all__ = ["DIALECTS", "Dialect", "DocumentContext"]


@dataclass(frozen=True)
class Dialect:
    """The markup of a document format.

    Attributes:
        printer: the printer of the math
        symbols: the dialect of the math symbols, see `symbols.typeset_symbol`
        text: the escaping of text
        code: an id as code, e.g. in a code span, or a part of a long id
        wbr: the opportunity of a line break between two parts of a long id as code,
            which writes no character, the empty string if the parts are not split
        text_wbr: the same between two parts of text, the empty string where it
            would write a character (the zero width space of typst is text of the
            PDF)
        superscript: an exponent of a unit as a superscript, from the exponent
        minus: the minus sign of a negative exponent in text, `−` (U+2212), not the
            hyphen
        derivative: the derivative of a symbol in time, `{symbol}` is replaced
        arrow: the arrow of an irreversible reaction
        reversible: the arrow of a reversible reaction
        empty: the side of a reaction without species
        thin: the space between a stoichiometry and its species
        brackets: a large opening and closing parenthesis which can be on different
            lines of an alignment
        new: the superscript of the new value of a variable, `{symbol}` is replaced
        times: the product in a unit, `mol·s`
        unit: the markup of a written unit, which keeps the letters of a unit
            apart, `fl` is no ligature
        pdf_text: the escaping of text in a string of the PDF, a bookmark, without
            math, `None` if it is `text`
    """

    printer: type[DocumentPrinter]
    symbols: Literal["latex", "typst"]
    text: Callable[[object], str]
    code: Callable[[str], str]
    wbr: str
    text_wbr: str
    superscript: Callable[[str], str]
    minus: str
    derivative: str
    arrow: str
    reversible: str
    empty: str
    thin: str
    brackets: tuple[str, str]
    new: str
    times: str
    unit: Callable[[str], str] = lambda unit: unit
    pdf_text: Callable[[object], str] | None = None


LONG_ID = 12
"""The length of an id from which on it may break after an underscore in a table."""


def _parts(sid: str) -> list[str]:
    """The parts of an id between which a line may break, after an underscore.

    An id of at most `LONG_ID` characters is a single part.
    """
    if len(sid) <= LONG_ID:
        return [sid]
    return re.findall(r"[^_]*_+|[^_]+$", sid)


# an f which forms a ligature with the next letter, `fl`, `ff`, `fi`
_LIGATURE = re.compile(r"f(?=[fil])")


def _latex(
    text: Callable[[object], str],
    code: Callable[[str], str],
    wbr: str,
    superscript: Callable[[str], str],
    minus: str,
    unit: Callable[[str], str] = lambda unit: unit,
    pdf_text: Callable[[object], str] | None = None,
) -> Dialect:
    """The markup of the math of LaTeX, with the markup of the text of a format."""
    return Dialect(
        printer=LatexPrinter,
        symbols="latex",
        text=text,
        code=code,
        wbr=wbr,
        text_wbr=wbr,
        superscript=superscript,
        minus=minus,
        derivative=r"\frac{\mathrm{d} {symbol}}{\mathrm{d} t}",
        arrow=r"\longrightarrow",
        reversible=r"\rightleftharpoons",
        empty=r"\varnothing",
        thin=r"\,",
        brackets=(r"\Bigl(", r"\Bigr)"),
        new=r"{symbol}^{\mathrm{new}}",
        times="·",
        unit=unit,
        pdf_text=pdf_text,
    )


DIALECTS: dict[str, Dialect] = {
    "typst": Dialect(
        printer=TypstPrinter,
        symbols="typst",
        text=typst_text,
        code=lambda sid: f"`{sid}`",
        wbr="#sym.zws;",
        text_wbr="",
        superscript=lambda exponent: f"#super[{exponent}]",
        minus="\u2212",
        derivative="(dif {symbol})/(dif t)",
        arrow="-->",
        reversible="harpoons.rtlb",
        empty="emptyset",
        thin="thin",
        brackets=("lr(size: #150%, \\()", "lr(size: #150%, \\))"),
        new='{symbol}^("new")',
        times="·",
        unit=lambda unit: (
            f"#text(ligatures: false)[{unit}]" if _LIGATURE.search(unit) else unit
        ),
    ),
    "latex": _latex(
        tex_text,
        lambda sid: rf"\texttt{{{tex_text(sid)}}}",
        r"\allowbreak{}",
        lambda exponent: rf"\textsuperscript{{{exponent}}}",
        r"\textminus{}",
        lambda unit: _LIGATURE.sub(r"f\\kern0pt{}", unit),
        tex_pdf_text,
    ),
    "markdown": _latex(
        markdown_text,
        lambda sid: f"`{sid}`",
        "",
        lambda exponent: f"<sup>{exponent}</sup>",
        "\u2212",
    ),
}
"""The markup of each document format, by the name of the format."""


# the exponent of a unit, `m^3`, `s^-1`, `m^0.5`
_EXPONENT = re.compile(r"\^(-?[0-9.]+)")

# the name of the new value of a compartment in the math of an event assignment,
# which is no SId, so that it is never the id of the model
_NEW = "new value of "


class DocumentContext:
    """The context of a document format, see the module."""

    def __init__(self, system: OdeSystem, fmt: str, symbols: str) -> None:
        """Prepare the context of a system.

        Args:
            system: the ODE system
            fmt: the name of the format, a key of `DIALECTS`
            symbols: `"id"` or `"name"`, what the math symbols are made of

        Raises:
            ValueError: for symbols which are neither `"id"` nor `"name"`
        """
        if symbols not in ("id", "name"):
            raise ValueError(
                f"The option 'symbols' is 'id' or 'name', not {symbols!r}."
            )
        self.system = system
        self.dialect = DIALECTS[fmt]
        self.printer = self.dialect.printer()
        self.symbols = self._symbols(symbols == "name")
        self.ruled = {
            a.variable for a in system.assignments if a.origin == "assignment_rule"
        }

    # --- symbols ------------------------------------------------------------------

    def _symbols(self, by_name: bool) -> dict[str, str]:
        """The math symbol of every id of the system.

        A reaction is `v` with its id (or name) as subscript, an amount `n` with the
        symbol of its species as subscript, unless the symbol is taken, then it is
        the symbol of its id.
        """
        system = self.system
        dialect = self.dialect.symbols
        ids = [q.symbol.sid for q in system.quantities]
        ids.extend(r.symbol.sid for r in system.reactions)
        ids.extend(f.symbol.sid for f in system.functions)
        names = None
        if by_name:
            names = {
                sid: str(system.symbol(sid).name)
                for sid in ids
                if system.symbol(sid).name
            }
        symbols = typeset_names(ids, dialect, names)
        taken = set(symbols.values())
        preferred: dict[str, str] = {}
        for reaction in system.reactions:
            sid = reaction.symbol.sid
            label = (names or {}).get(sid, sid)
            if not re.fullmatch(r"[A-Za-z0-9_]+", label):
                label = sid
            preferred[sid] = typeset_symbol(f"v_{label}", dialect)
        for amount in system.amounts:
            species = symbols[str(amount.amount_of)]
            preferred[amount.symbol.sid] = (
                f"n_{{{species}}}" if dialect == "latex" else f"n_({species})"
            )
        for sid, symbol in preferred.items():
            if symbol not in taken:
                taken.discard(symbols[sid])
                symbols[sid] = symbol
                taken.add(symbol)
        return symbols

    # --- printing -----------------------------------------------------------------

    def math(self, ast: libsbml.ASTNode | None) -> str | None:
        """The math of a number, `None` without math."""
        return None if ast is None else self.printer.print(ast, self.symbols)

    def condition(self, ast: libsbml.ASTNode) -> str:
        """The math of a condition, e.g. a trigger."""
        return self.printer.print_condition(ast, self.symbols)

    def lines(self, ast: libsbml.ASTNode) -> list[str]:
        """The math of a number in lines of at most four terms."""
        return self.printer.print_lines(ast, self.symbols)

    def number(self, value: float | None) -> str | None:
        """The math of a number, `None` without a value."""
        if value is None:
            return None
        return self.printer.number(value)

    def text(self, value: object) -> str | None:
        """Escaped text, `None` without text."""
        return None if value is None or value == "" else self.dialect.text(value)

    def code(self, sid: str) -> str:
        """An id as code, a long id with opportunities of line breaks after `_`.

        Raises:
            ValueError: if the id is not an SId, which could end the code and write
                markup, libsbml reads a document with an invalid id
        """
        check_sid(sid)
        return self._code(sid)

    def label(self, element: str) -> str:
        """The label of an element as code, an SId or a metaid (an XML ID).

        Raises:
            ValueError: if the label is neither an SId nor an XML ID
        """
        if not libsbml.SyntaxChecker.isValidXMLID(element):
            check_sid(element)
        return self._code(element)

    def _code(self, sid: str) -> str:
        """An id or a label which is checked as code."""
        if not self.dialect.wbr:
            return self.dialect.code(sid)
        return self.dialect.wbr.join(self.dialect.code(part) for part in _parts(sid))

    def breakable(self, value: str) -> str:
        """Escaped text which may break after an underscore if it is long, a file name."""
        parts = _parts(value)
        return self.dialect.text_wbr.join(self.dialect.text(part) for part in parts)

    def unit(self, unit: str | None) -> str | None:
        """A unit as escaped text, its exponents as superscripts, `m³`."""
        if not unit:
            return None
        parts = _EXPONENT.split(unit)
        written = []
        for k, part in enumerate(parts):
            if k % 2:
                exponent = self.dialect.text(part.removeprefix("-"))
                if part.startswith("-"):
                    exponent = self.dialect.minus + exponent
                written.append(self.dialect.superscript(exponent))
            elif part:
                factors = (self.dialect.text(factor) for factor in part.split("*"))
                written.append(self.dialect.times.join(factors))
        return self.dialect.unit("".join(written))

    # --- the sections -------------------------------------------------------------

    def build(self, options: Mapping[str, object]) -> dict[str, object]:
        """The context, see the module."""
        system = self.system
        info = system.info
        if info.sid is not None:
            check_sid(info.sid)
        if info.name:
            title = self.dialect.text(info.name)
            plain = (self.dialect.pdf_text or self.dialect.text)(info.name)
        else:
            # an id may break after an underscore
            title = self.breakable(info.sid or "Model")
            plain = self.dialect.text(info.sid or "Model")
        return {
            "model": {
                "title": title,
                "plain_title": plain,
                "id": None if info.sid is None else self.code(info.sid),
                "level": info.level,
                "version": info.version,
                "source": None if info.source is None else self.breakable(info.source),
                "sbmlutils": sbmlutils.__version__,
                "notes": [
                    self.dialect.text(paragraph)
                    for paragraph in (info.notes or "").split("\n\n")
                    if paragraph.strip()
                ],
            },
            "units": [
                {"kind": kind, "unit": self.unit(unit)}
                for kind, unit in info.units.items()
                if unit
            ],
            "compartments": [self.row(q) for q in system.compartments],
            "species": [self.species_row(q) for q in system.species],
            "parameters": [
                self.row(q) for q in (*system.parameters, *system.species_references)
            ],
            "functions": [self.function(k) for k in range(len(system.functions))],
            "initial": [
                {
                    "lhs": self.symbols[a.variable],
                    "lines": self.lines(a.math),
                    "origin": a.origin,
                }
                for a in system.initial
                if a.origin == "initial_assignment"
                or (a.origin == "initial_value" and not is_number(a.math))
            ],
            "assignments": [
                {
                    "lhs": self.symbols[a.variable],
                    "lines": self.lines(a.math),
                    "origin": a.origin,
                }
                for a in system.assignments
                if a.origin in ("assignment_rule", "concentration")
            ],
            "amounts": [
                {
                    "amount": self.symbols[q.symbol.sid],
                    "species": self.symbols[str(q.amount_of)],
                    "compartment": self.symbols[str(q.compartment)],
                }
                for q in system.amounts
            ],
            "reactions": [self.reaction(k) for k in range(len(system.reactions))],
            "odes": [self.ode(ode) for ode in system.odes],
            "events": [self.event(k) for k in range(len(system.events))],
            "unsupported": [
                {"construct": self.dialect.text(construct), "id": self.label(sid)}
                for construct, sid in system.unsupported
            ],
            "options": dict(options),
        }

    def row(self, quantity: Quantity) -> dict[str, object]:
        """The row of a compartment or a parameter in its table."""
        symbol = quantity.symbol
        return {
            "symbol": self.symbols[symbol.sid],
            "id": self.code(symbol.sid),
            "long_id": len(symbol.sid) > LONG_ID,
            "name": self.text(symbol.name),
            # the value of a quantity with a rule is the value of its rule
            "value": None if symbol.sid in self.ruled else self.number(quantity.value),
            "unit": self.unit(symbol.unit),
            "constant": quantity.constant,
        }

    def species_row(self, quantity: Quantity) -> dict[str, object]:
        """The row of a species in its table."""
        properties = ["amount" if quantity.amount else "concentration"]
        if quantity.boundary:
            properties.append("boundary")
        if quantity.constant:
            properties.append("constant")
        return {
            **self.row(quantity),
            "compartment": (
                self.symbols[quantity.compartment] if quantity.compartment else None
            ),
            "properties": self.dialect.text(", ".join(properties)),
        }

    def function(self, index: int) -> dict[str, object]:
        """A function definition, `f(x, y) = ...`."""
        function = self.system.functions[index]
        dialect = self.dialect.symbols
        functions = {
            f.symbol.sid: self.symbols[f.symbol.sid] for f in self.system.functions
        }
        arguments = {a: typeset_symbol(a, dialect) for a in function.arguments}
        lhs = self.printer.call(
            self.symbols[function.symbol.sid],
            [Printed(arguments[a], Precedence.ATOM) for a in function.arguments],
        ).code
        return {
            "id": self.code(function.symbol.sid),
            "name": self.text(function.symbol.name),
            "lhs": lhs,
            "rhs": self.printer.print(function.body, {**functions, **arguments}),
        }

    def _side(self, participants: Sequence[Participant]) -> str:
        """A side of a reaction equation, `2 A + B`, `∅` without species."""
        if not participants:
            return self.dialect.empty
        terms = []
        for participant in participants:
            species = self.symbols[participant.species]
            stoichiometry = participant.stoichiometry
            if isinstance(stoichiometry, str):
                factor: str | None = self.symbols[stoichiometry]
            elif stoichiometry == 1.0:
                factor = None
            else:
                factor = self.number(stoichiometry)
            terms.append(
                f"{factor} {self.dialect.thin} {species}" if factor else species
            )
        return " + ".join(terms)

    def reaction(self, index: int) -> dict[str, object]:
        """A reaction: its equation and its rate."""
        reaction = self.system.reactions[index]
        arrow = self.dialect.reversible if reaction.reversible else self.dialect.arrow
        equation = (
            f"{self._side(reaction.reactants)} {arrow} {self._side(reaction.products)}"
        )
        return {
            "symbol": self.symbols[reaction.symbol.sid],
            "id": self.code(reaction.symbol.sid),
            "long_id": len(reaction.symbol.sid) > LONG_ID,
            "name": self.text(reaction.symbol.name),
            "equation": equation,
            "modifiers": ", ".join(self.symbols[m] for m in reaction.modifiers) or None,
            "local_parameters": ", ".join(
                self.symbols[p] for p in reaction.local_parameters
            )
            or None,
            "lines": self.lines(reaction.rate),
        }

    def ode(self, ode: Ode) -> dict[str, object]:
        """The ODE of a state, with the rates of the reactions.

        The reaction terms of a species in concentration are divided by its volume,
        `(v_1 - v_2)/V`, or in lines `1/V (v_1 - v_2 ...)`.
        """
        if ode.origin == "rate_rule" or ode.reaction_terms is None:
            lines = self.lines(ode.rhs)
        elif ode.volume is None:
            lines = self.lines(ode.reaction_terms)
        else:
            lines = self.lines(ode.reaction_terms)
            volume = Printed(self.symbols[ode.volume], Precedence.ATOM)
            if len(lines) == 1:
                ast = node(
                    libsbml.AST_DIVIDE, ode.reaction_terms.deepCopy(), name(ode.volume)
                )
                lines = [self.printer.print(ast, self.symbols)]
            else:
                one = Printed(self.printer.integer(1), Precedence.ATOM)
                factor = self.printer.divide(one, volume).code
                left, right = self.dialect.brackets
                lines[0] = f"{factor} {left} {lines[0]}"
                lines[-1] = f"{lines[-1]} {right}"
        symbol = self.symbols[ode.variable]
        # a symbol of upright letters is set apart from the upright d, d PX; typst
        # spaces a string of letters without a subscript as a word itself
        if symbol.startswith(r"\mathrm"):
            symbol = rf"\,{symbol}"
        elif symbol.startswith("upright(") and ")_(" in symbol:
            symbol = f"thin {symbol}"
        return {
            "lhs": self.dialect.derivative.replace("{symbol}", symbol),
            "lines": lines,
            "origin": ode.origin,
        }

    def event(self, index: int) -> dict[str, object]:
        """An event: its trigger, delay, priority, flags and assignments."""
        event = self.system.events[index]
        symbol = event.symbol
        assignments = [self.event_assignment(a) for a in event.assignments]
        return {
            "id": self.code(symbol.sid),
            "name": self.text(symbol.name),
            "trigger": self.condition(event.trigger),
            "delay": self.math(event.delay),
            "priority": self.math(event.priority),
            "initial_value": event.initial_value,
            "persistent": event.persistent,
            "use_trigger_values": event.use_values_from_trigger_time,
            "assignments": assignments,
        }

    def event_assignment(self, assignment: EventAssignment) -> dict[str, str | None]:
        """An event assignment with its effective value, `value · scale / new(divisor)`.

        The conversion of a size is `amount`, the value of an amount is a
        concentration times the size of its compartment, or `resized`, a
        concentration is converted to the new size of its compartment, see
        `system.EventAssignment`.
        """
        factors = []
        # a concentration of 1 converted to an amount is the size, `n_A := V`
        if assignment.math is not None and not (
            assignment.scale is not None and is_number(assignment.math, 1.0)
        ):
            factors.append(assignment.math.deepCopy())
        if assignment.scale is not None:
            factors.append(assignment.scale.deepCopy())
        value = product(factors) if factors else _one()
        symbols = dict(self.symbols)
        conversion = None
        compartment = None
        new = None
        quantity = self.system.quantity(assignment.variable)
        if assignment.divisor is not None:
            conversion = "resized"
            compartment = self.symbols[assignment.divisor]
            new = self.dialect.new.replace("{symbol}", compartment)
            symbols[_NEW + assignment.divisor] = new
            value = node(libsbml.AST_DIVIDE, value, name(_NEW + assignment.divisor))
        elif assignment.scale is not None and quantity.amount_of is not None:
            conversion = "amount"
            compartment = self.symbols[str(quantity.compartment)]
        return {
            "lhs": self.symbols[assignment.variable],
            "rhs": self.printer.print(value, symbols),
            "conversion": conversion,
            "species": None
            if quantity.amount_of is None
            else self.symbols[quantity.amount_of],
            "compartment": compartment,
            "new": new,
        }


def _one() -> libsbml.ASTNode:
    """The integer 1."""
    ast = libsbml.ASTNode(libsbml.AST_INTEGER)
    ast.setValue(1)
    return ast
