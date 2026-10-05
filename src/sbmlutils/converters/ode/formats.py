"""The formats of the ODE export: their registry, rendering context and templates.

A format is a jinja2 template in `sbmlutils/resources/converters/ode` with the math
printer of its language (`Format`, `FORMATS`): code which simulates the model (python,
julia, R, option `simulator`) or a document which describes it (typst, LaTeX,
markdown, options `standalone` and `symbols`). `render` checks the options against
the format, builds the names of the symbols in the format (`symbols.code_names` for
code, `symbols.typeset_names` for documents), prints every math of the system once
with the printer and renders the template with the context of `context`: plain
strings, numbers, booleans, lists and dicts, so that a template never touches
libsbml. The context of a document is described in `documents`, it holds text and
math as markup of the format.

The context of a code format holds:

- `model`: id, name, level, version, source (the file name), units (time, substance,
  extent, volume, area, length), `sbmlutils`, the version which writes the code, and
  `module`, the name of a module of the model in the code (`module <name>` in
  julia), see `_CodeContext.module_name`;
- `states`, `constants`, `assigned`: the variables of the vectors x, p and y, each a
  dict with `id`, `name`, `unit`, `code` (the name in the code), `index` (from
  `Format.first_index`), `value` (a literal of the default value, `None` if it has
  none), `comment` (name and unit, e.g. `species A [mmol/l]`, without a name which
  is the id), `kind` (of the symbol, e.g. `species`) and `amount_of`, the species
  whose amount it is;
- `functions`: the function definitions with `code`, `name`, `arguments` (their
  names in the code) and `body`;
- `initial`, `assignments`: the initial values at t=0 and the assignments (rules,
  concentrations of amounts, reaction rates) in the order of their evaluation, each
  with `id`, `code`, `expr`, `comment`, `origin` and `role`; a reaction rate is
  written under the id of its reaction;
- `odes`: the right hand side of each state with `id`, `code`, `index`, `expr` and
  `comment`;
- `events`: each event with `id`, `code`, `name`, `comment` (the name, without a
  name which is the id), `trigger` (a condition), `root` (its continuous root
  function), `initial_value`, `persistent`, `delay`, `priority`,
  `use_trigger_values`, `assignments`, each with `id`, `code`, `kind` (`state` or
  `constant`), `index`, `comment`, `expr`, `scale` and `divisor_position` (the
  0-based position in `assignments` of the assignment whose new value divides it,
  independent of `Format.first_index`, see `system.EventAssignment`), `functions`,
  the names of the functions the code writes for the event (`delay`, `priority`,
  `values`, `assign`, unique against the names of the ids and the reserved names
  of the language; `delay` and `priority` are `None` without math), and `scopes`,
  the scope of each of these functions (`assign` the scope of the scales); a
  template reads the key `values` as `functions["values"]`, `functions.values` is
  the method of the dict;
- `event_constants`: the constants which an event assigns, entries of `constants`
  in their order, which change in time like the states;
- `scopes`: for each function of the code (`initial`, `dxdt`, `y`, `triggers` of
  the conditions of the triggers, `roots` of their root functions) what it uses:
  the `states` and `constants` it unpacks, the `assignments` it evaluates (a
  subset of `initial` or `assignments`, in their order) and whether its math uses
  the `time`; `initial` additionally holds the `computed` constants, which it
  writes into p, each with the `origin` of its initial value
  (`initial_assignment` or `initial_value`, a conversion with another quantity);
- `modules`: the modules of the language the printed math uses, of
  `MathPrinter.MODULES` and `MathPrinter.IMPORTED`, e.g. `math`;
- `options`: the options of the rendering.

Every name and unit is a single line (`text.single_line`); a template which writes
text into a string or a docstring escapes it with the filters of its language.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import jinja2
import libsbml

import sbmlutils
from sbmlutils import RESOURCES_DIR
from sbmlutils.converters.ode.astutil import walk
from sbmlutils.converters.ode.dependencies import names
from sbmlutils.converters.ode.documents import DocumentContext
from sbmlutils.converters.ode.printers import PRINTERS, MathPrinter
from sbmlutils.converters.ode.symbols import RESERVED, code_names
from sbmlutils.converters.ode.text import check_sid, single_line

if TYPE_CHECKING:
    from sbmlutils.converters.ode.system import OdeSystem, Quantity, Symbol

__all__ = [
    "FORMATS",
    "TEMPLATE_DIR",
    "Format",
    "context",
    "render",
    "render_template",
    "write",
]

TEMPLATE_DIR: Path = RESOURCES_DIR / "converters" / "ode"
"""The directory of the templates of the formats."""


@dataclass(frozen=True)
class Format:
    """An output format of the ODE export.

    Attributes:
        name: the name, e.g. `"python"`
        kind: `"code"`, which simulates the model, or `"document"`, which describes it
        template: the file name of the template in `TEMPLATE_DIR`
        suffixes: the file suffixes `write` takes the format from, case sensitive
        printer: the key of the math printer in `printers.PRINTERS`, for code also
            the language of `symbols.code_names`
        options: the options the format accepts with their defaults
        first_index: the index of the first element of a vector, 0 in python, 1 in
            julia and R
    """

    name: str
    kind: Literal["code", "document"]
    template: str
    suffixes: tuple[str, ...]
    printer: str
    options: Mapping[str, object] = field(default_factory=dict)
    first_index: int = 0


FORMATS: dict[str, Format] = {
    "python": Format(
        name="python",
        kind="code",
        template="python.py.jinja",
        suffixes=(".py",),
        printer="python",
        options={"simulator": True},
    ),
    "julia": Format(
        name="julia",
        kind="code",
        template="julia.jl.jinja",
        suffixes=(".jl",),
        printer="julia",
        options={"simulator": True},
        first_index=1,
    ),
    "r": Format(
        name="r",
        kind="code",
        template="r.R.jinja",
        suffixes=(".R", ".r"),
        printer="r",
        options={"simulator": True},
        first_index=1,
    ),
    "typst": Format(
        name="typst",
        kind="document",
        template="typst.typ.jinja",
        suffixes=(".typ",),
        printer="typst",
        options={"standalone": True, "symbols": "id"},
    ),
    "latex": Format(
        name="latex",
        kind="document",
        template="latex.tex.jinja",
        suffixes=(".tex",),
        printer="latex",
        options={"standalone": True, "symbols": "id"},
    ),
    "markdown": Format(
        name="markdown",
        kind="document",
        template="markdown.md.jinja",
        suffixes=(".md",),
        printer="latex",
        options={"standalone": True, "symbols": "id"},
    ),
}
"""The formats by their name."""


# --- options --------------------------------------------------------------------------


def _format(fmt: str) -> Format:
    """The format of a name, `ValueError` if there is none."""
    try:
        return FORMATS[fmt]
    except KeyError:
        raise ValueError(
            f"There is no format {fmt!r}, use one of {sorted(FORMATS)}."
        ) from None


def _options(fmt: Format, options: Mapping[str, object]) -> dict[str, object]:
    """The options of a rendering: the defaults of the format, updated with `options`.

    Raises:
        ValueError: for an option the format does not accept and for a value of
            another type than its default
    """
    merged = dict(fmt.options)
    for key, value in options.items():
        if key not in fmt.options:
            raise ValueError(
                f"The format {fmt.name!r} has no option {key!r}, "
                f"its options are {sorted(fmt.options)}."
            )
        default = fmt.options[key]
        if type(value) is not type(default):
            raise ValueError(
                f"The option {key!r} of the format {fmt.name!r} is a "
                f"{type(default).__name__}, not {value!r}."
            )
        merged[key] = value
    return merged


def _check_code(system: OdeSystem, fmt: Format) -> None:
    """Check that the system can be written as code.

    Raises:
        NotImplementedError: if the model uses a construct the code does not support
    """
    if fmt.kind == "code" and system.unsupported:
        listed = ", ".join(
            f"{construct} {sid!r}" for construct, sid in system.unsupported
        )
        raise NotImplementedError(
            f"The model uses constructs the {fmt.name} code does not support: {listed}."
        )


# --- the context ----------------------------------------------------------------------


def _comment(symbol: Symbol) -> str:
    """The name and the unit of a symbol on a single line, `name [unit]`.

    A name which is the id is left out, the comment stands next to the id.
    """
    parts = []
    if symbol.name and symbol.name != symbol.sid:
        parts.append(single_line(symbol.name))
    if symbol.unit:
        parts.append(f"[{single_line(symbol.unit)}]")
    return " ".join(parts)


def _uses_time(ast: libsbml.ASTNode | None) -> bool:
    """Whether a math uses the time."""
    return ast is not None and any(
        node.getType() == libsbml.AST_NAME_TIME for node in walk(ast)
    )


def _needed(
    used: Iterable[str], maths: Mapping[str, libsbml.ASTNode | None]
) -> set[str]:
    """The ids which are used, with the ids their math uses, transitively.

    Args:
        used: the ids which are used
        maths: the math of the ids which are computed

    Returns:
        the ids used directly or by the math of a used id
    """
    needed: set[str] = set()
    pending = list(used)
    while pending:
        sid = pending.pop()
        if sid in needed:
            continue
        needed.add(sid)
        if sid in maths:
            pending.extend(names(maths[sid]))
    return needed


def _scope(
    entries: Mapping[str, Sequence[dict[str, object]]],
    used: set[str],
    evaluated: Sequence[dict[str, object]],
    time: bool,
    computed: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """The scope of a function of the code, see the module.

    Args:
        entries: the entries of the `states` and the `constants`
        used: the ids the function uses, directly or through an assignment
        evaluated: the assignments the function can evaluate, in their order
        time: whether the math of the function uses the time
        computed: the origin of each constant the function computes

    Returns:
        the states and constants it unpacks, the assignments it evaluates, whether
        it uses the time and the constants it computes
    """
    computed = computed or {}
    computed_ids = {str(a["id"]) for a in evaluated}
    unpacked = used - computed_ids
    return {
        "states": [x for x in entries["states"] if x["id"] in unpacked],
        "constants": [c for c in entries["constants"] if c["id"] in unpacked],
        "assignments": [a for a in evaluated if a["id"] in used],
        "time": time,
        "computed": [
            {**c, "origin": computed[str(c["id"])]}
            for c in entries["constants"]
            if c["id"] in computed
        ],
    }


class _CodeContext:
    """The context of a code format, see the module."""

    def __init__(self, system: OdeSystem, fmt: Format) -> None:
        self.system = system
        self.fmt = fmt
        self.printer: MathPrinter = PRINTERS[fmt.printer]()
        ids = [q.symbol.sid for q in system.quantities]
        ids.extend(r.symbol.sid for r in system.reactions)
        ids.extend(f.symbol.sid for f in system.functions)
        ids.extend(e.symbol.sid for e in system.events)
        self.codes = code_names(ids, fmt.printer)
        self.quantities = {q.symbol.sid: q for q in system.quantities}
        self.printed: list[str] = []
        # the names of the functions the code writes for the events
        self.taken = set(self.codes.values()) | RESERVED[fmt.printer]

    def unique(self, name: str) -> str:
        """A name of a generated function, unique against the ids and reserved names."""
        while name in self.taken:
            name += "_"
        self.taken.add(name)
        return name

    def expr(self, ast: libsbml.ASTNode | None, condition: bool = False) -> str | None:
        """The printed math, `None` without math."""
        if ast is None:
            return None
        if condition:
            code = self.printer.print_condition(ast, self.codes)
        else:
            code = self.printer.print(ast, self.codes)
        self.printed.append(code)
        return code

    def value(self, value: float | None) -> str | None:
        """The literal of a value, `None` without a value."""
        return None if value is None else self.printer.number(value)

    def variable(self, sid: str, index: int) -> dict[str, object]:
        """The entry of a variable of a vector."""
        quantity: Quantity | None = self.quantities.get(sid)
        symbol = self.system.symbol(sid)
        return {
            "id": sid,
            "name": single_line(symbol.name) if symbol.name else None,
            "unit": single_line(symbol.unit) if symbol.unit else None,
            "code": self.codes[sid],
            "index": index + self.fmt.first_index,
            "value": self.value(quantity.value) if quantity else None,
            "comment": _comment(symbol),
            "kind": symbol.kind,
            "amount_of": quantity.amount_of if quantity else None,
        }

    def assignment(
        self, variable: str, ast: libsbml.ASTNode, origin: str
    ) -> dict[str, object]:
        """The entry of an assignment or an initial value."""
        quantity = self.quantities.get(variable)
        return {
            "id": variable,
            "code": self.codes[variable],
            "expr": self.expr(ast),
            "comment": _comment(self.system.symbol(variable)),
            "origin": origin,
            "role": "assigned" if quantity is None else quantity.role,
        }

    def function(self, index: int) -> dict[str, object]:
        """The entry of a function definition, its arguments named in the code."""
        function = self.system.functions[index]
        functions = {
            f.symbol.sid: self.codes[f.symbol.sid] for f in self.system.functions
        }
        arguments = code_names(function.arguments, self.fmt.printer)
        taken = set(functions.values())
        for argument, code in arguments.items():
            while code in taken:
                code += "_"
            taken.add(code)
            arguments[argument] = code
        body = self.printer.print(function.body, {**functions, **arguments})
        self.printed.append(body)
        return {
            "id": function.symbol.sid,
            "code": self.codes[function.symbol.sid],
            "name": single_line(function.symbol.name) if function.symbol.name else None,
            "arguments": [arguments[a] for a in function.arguments],
            "body": body,
        }

    def build(self, options: Mapping[str, object]) -> dict[str, object]:
        """The context.

        Raises:
            ValueError: if the id of the model is not an SId, which the code writes
                as the name of a module (julia) and into a comment (R)
        """
        system = self.system
        info = system.info
        if info.sid is not None:
            check_sid(info.sid)
        states = [self.variable(sid, k) for k, sid in enumerate(system.states)]
        constants = [self.variable(sid, k) for k, sid in enumerate(system.constants)]
        assigned = [self.variable(sid, k) for k, sid in enumerate(system.assigned)]
        by_id = {str(v["id"]): v for v in (*states, *constants)}
        functions = [self.function(k) for k in range(len(system.functions))]
        initial = [
            self.assignment(a.variable, a.math, a.origin) for a in system.initial
        ]
        assignments = [
            self.assignment(a.variable, a.math, a.origin) for a in system.assignments
        ]
        odes = [
            {
                "id": ode.variable,
                "code": self.codes[ode.variable],
                "index": k + self.fmt.first_index,
                "expr": self.expr(ode.rhs),
                "comment": _comment(system.symbol(ode.variable)),
            }
            for k, ode in enumerate(system.odes)
        ]
        # the entries the scopes of the functions of the events refer to
        self.entries = {
            "states": states,
            "constants": constants,
            "assignments": assignments,
        }
        events = [self.event(k, by_id) for k in range(len(system.events))]
        assigned_by_events = {a.variable for e in system.events for a in e.assignments}
        event_constants = [c for c in constants if c["id"] in assigned_by_events]
        return {
            "model": {
                "id": info.sid,
                "name": single_line(info.name) if info.name else None,
                "level": info.level,
                "version": info.version,
                "source": single_line(info.source) if info.source else None,
                "units": {
                    key: single_line(unit) if unit else None
                    for key, unit in info.units.items()
                },
                "sbmlutils": sbmlutils.__version__,
                "module": self.module_name(),
            },
            "states": states,
            "constants": constants,
            "assigned": assigned,
            "functions": functions,
            "initial": initial,
            "assignments": assignments,
            "odes": odes,
            "events": events,
            "event_constants": event_constants,
            "scopes": self.scopes(initial),
            "modules": self.modules(),
            "options": dict(options),
        }

    def event(
        self, index: int, by_id: Mapping[str, dict[str, object]]
    ) -> dict[str, object]:
        """The entry of an event."""
        event = self.system.events[index]
        variables = [a.variable for a in event.assignments]
        assignments = []
        for a in event.assignments:
            variable = by_id[a.variable]
            assignments.append(
                {
                    "id": a.variable,
                    "code": self.codes[a.variable],
                    "kind": "state" if a.variable in self.system.states else "constant",
                    "index": variable["index"],
                    "comment": variable["comment"],
                    "expr": self.expr(a.math),
                    "scale": self.expr(a.scale),
                    "divisor_position": None
                    if a.divisor is None
                    else variables.index(a.divisor),
                }
            )
        symbol = event.symbol
        code = self.codes[symbol.sid]
        values = [a.math for a in event.assignments]
        scales = [a.scale for a in event.assignments]
        return {
            "id": symbol.sid,
            "code": code,
            "name": single_line(symbol.name) if symbol.name else None,
            "comment": _comment(symbol),
            "trigger": self.expr(event.trigger, condition=True),
            "root": self.expr(event.root),
            "initial_value": event.initial_value,
            "persistent": event.persistent,
            "delay": self.expr(event.delay),
            "priority": self.expr(event.priority),
            "use_trigger_values": event.use_values_from_trigger_time,
            "assignments": assignments,
            "functions": {
                "delay": None
                if event.delay is None
                else self.unique(f"event_delay_{code}"),
                "priority": None
                if event.priority is None
                else self.unique(f"event_priority_{code}"),
                "values": self.unique(f"event_values_{code}"),
                "assign": self.unique(f"event_assign_{code}"),
            },
            "scopes": {
                "delay": self.math_scope([event.delay]),
                "priority": self.math_scope([event.priority]),
                "values": self.math_scope(values),
                "assign": self.math_scope(scales),
            },
        }

    def math_scope(self, maths: Sequence[libsbml.ASTNode | None]) -> dict[str, object]:
        """The scope of a function which evaluates math at a state, as `f_y`.

        Args:
            maths: the math the function evaluates, `None` for none

        Returns:
            the states and constants the math uses, the assignments it needs and
            whether it uses the time, see the module
        """
        rules = {a.variable: a.math for a in self.system.assignments}
        used = _needed(set().union(set(), *(names(m) for m in maths)), rules)
        time = any(_uses_time(m) for m in maths) or any(
            _uses_time(rules[sid]) for sid in used if sid in rules
        )
        return _scope(self.entries, used, self.entries["assignments"], time)

    def scopes(
        self, initial: Sequence[dict[str, object]]
    ) -> dict[str, dict[str, object]]:
        """What each function of the code uses, so that it computes nothing unused."""
        system = self.system
        entries = self.entries
        assignments = entries["assignments"]

        # the initial values: the states and the constants they set, and what these use
        maths = {a.variable: a.math for a in system.initial}
        computed = {
            a.variable: a.origin
            for a in system.initial
            if a.variable in system.constants
        }
        used = _needed([*system.states, *computed], maths)
        time = any(_uses_time(a.math) for a in system.initial if a.variable in used)
        initial_scope = _scope(entries, used, initial, time, computed)

        # the rates of change: the odes and the assignments they use
        maths = {a.variable: a.math for a in system.assignments}
        used = _needed(set().union(*(names(o.rhs) for o in system.odes)), maths)
        time = any(_uses_time(o.rhs) for o in system.odes) or any(
            _uses_time(a.math) for a in system.assignments if a.variable in used
        )
        dxdt = _scope(entries, used, assignments, time)

        # the assigned values: every assignment
        used = _needed(system.assigned, maths)
        y = _scope(
            entries,
            used,
            assignments,
            any(_uses_time(a.math) for a in system.assignments),
        )

        # the triggers of the events, as conditions and as root functions
        triggers = self.math_scope([e.trigger for e in system.events])
        roots = self.math_scope([e.root for e in system.events])
        return {
            "initial": initial_scope,
            "dxdt": dxdt,
            "y": y,
            "triggers": triggers,
            "roots": roots,
        }

    def modules(self) -> list[str]:
        """The modules of the printer the printed math uses, e.g. `np` and `math`.

        A module of `MathPrinter.MODULES` is used where a member is written with it,
        `np.sin`, a module of `MathPrinter.IMPORTED` where its function is called,
        `gamma(`.
        """
        used = {
            module
            for module in self.printer.MODULES
            if any(
                re.search(rf"(?<![\w.]){re.escape(module)}\.", code)
                for code in self.printed
            )
        }
        used.update(
            module
            for function, module in self.printer.IMPORTED.items()
            if any(
                re.search(rf"(?<![\w.]){re.escape(function)}\(", code)
                for code in self.printed
            )
        )
        return sorted(used)

    def module_name(self) -> str:
        """The name of a module of the model in the code.

        The id of the model with its first letter upper-cased, `Model` for a model
        without an id, an id of underscores only (which julia cannot read) prefixed
        with `Model`; unique against the names of the ids and the reserved names.
        """
        sid = self.system.info.sid
        if not sid:
            name = "Model"
        elif not sid.strip("_"):
            name = f"Model{sid}"
        else:
            name = sid[0].upper() + sid[1:]
        return self.unique(name)


def context(
    system: OdeSystem, fmt: Format, options: Mapping[str, object]
) -> dict[str, object]:
    """The context a template of a format is rendered with, see the module.

    Args:
        system: the ODE system
        fmt: the format
        options: the options of the rendering

    Returns:
        the context, plain data

    Raises:
        ValueError: for the option `symbols` of a document which is neither `"id"`
            nor `"name"`
    """
    if fmt.kind == "document":
        symbols = str(options.get("symbols", "id"))
        return DocumentContext(system, fmt.name, symbols).build(options)
    return _CodeContext(system, fmt).build(options)


# --- the filters of the templates -----------------------------------------------------


def python_string(value: object) -> str:
    """A python string literal of text on a single line, `None` for `None`.

    Args:
        value: the text

    Returns:
        the literal in double quotes
    """
    return "None" if value is None else f'"{docstring(value)}"'


def docstring(value: object) -> str:
    """Text on a single line which is safe inside a python docstring.

    The backslash and the double quote are escaped, so that the text can neither end
    the docstring nor form an escape sequence.

    Args:
        value: the text

    Returns:
        the escaped text
    """
    return single_line(value).replace("\\", "\\\\").replace('"', '\\"')


def julia_text(value: object) -> str:
    """Text on a single line which is safe inside a julia string or docstring.

    The backslash, the double quote and the dollar sign are escaped, so that the text
    can neither end the string, form an escape sequence nor interpolate code,
    `$(...)`.

    Args:
        value: the text

    Returns:
        the escaped text
    """
    return (
        single_line(value).replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")
    )


def julia_string(value: object) -> str:
    """A julia string literal of text on a single line, `nothing` for `None`.

    Args:
        value: the text

    Returns:
        the literal in double quotes
    """
    return "nothing" if value is None else f'"{julia_text(value)}"'


def r_text(value: object) -> str:
    r"""Text on a single line which is safe inside an R string, of ASCII only.

    The backslash and the double quote are escaped, so that the text can neither end
    the string nor form an escape sequence, and every character which is not ASCII is
    written as its escape `\u{...}` (`\U{...}` beyond the basic plane), so that the
    string is the same in every locale R reads the file in.

    Args:
        value: the text

    Returns:
        the escaped text
    """
    text = single_line(value).replace("\\", "\\\\").replace('"', '\\"')
    return "".join(char if char.isascii() else _r_escape(char) for char in text)


def _r_escape(char: str) -> str:
    r"""The escape of a character in an R string, `\u{e4}` for `ä`."""
    code = ord(char)
    return f"\\u{{{code:04x}}}" if code <= 0xFFFF else f"\\U{{{code:08x}}}"


def r_string(value: object) -> str:
    """An R string literal of text on a single line, `NA_character_` for `None`.

    Args:
        value: the text

    Returns:
        the literal in double quotes
    """
    return "NA_character_" if value is None else f'"{r_text(value)}"'


def wrapped(
    items: Sequence[object],
    indent: int,
    column: int,
    tail: int = 1,
    width: int = 88,
    brackets: Sequence[str] = ("[", "]"),
    trailing: bool = True,
) -> str:
    """A list of items in brackets, on one line if it fits, else a block of lines.

    The block holds the items separated by commas on lines of at most `width`
    characters, indented by four spaces more than the line of the list, and closes
    with the bracket on a line of its own:

    ```python
    y = np.array([
        a, b, c,
        d,
    ])
    ```

    Args:
        items: the items, e.g. the names of a vector
        indent: the indentation of the line of the list
        column: the column of the opening bracket
        tail: the number of characters which follow the list on its line
        width: the width of a line
        brackets: the opening and the closing bracket, e.g. `("c(", ")")` in R
        trailing: whether the last item of a block is followed by a comma, which R
            does not allow

    Returns:
        the list from its opening to its closing bracket
    """
    opening, closing = brackets
    texts = [str(item) for item in items]
    single = f"{opening}{', '.join(texts)}{closing}"
    if column + len(single) + tail <= width:
        return single
    inner = " " * (indent + 4)
    lines: list[str] = []
    line = ""
    for text in texts:
        candidate = f"{line} {text}," if line else f"{text},"
        if line and len(inner) + len(candidate) > width:
            lines.append(line)
            line = f"{text},"
        else:
            line = candidate
    lines.append(line if trailing else line.removesuffix(","))
    body = "\n".join(inner + line for line in lines)
    return f"{opening}\n{body}\n{' ' * indent}{closing}"


def table(
    rows: Iterable[Sequence[object]],
    indent: int = 0,
    escape: Callable[[object], str] = single_line,
) -> str:
    """Rows of text as aligned columns, separated by two spaces.

    Args:
        rows: the rows, each a sequence of cells, `None` is an empty cell
        indent: the indentation of every line
        escape: the escaping of a cell, e.g. `docstring`

    Returns:
        the lines, without trailing spaces
    """
    cells = [["" if c is None else escape(c) for c in row] for row in rows]
    if not cells:
        return ""
    widths = [max(len(row[k]) for row in cells) for k in range(len(cells[0]))]
    lines = [
        " " * indent + "  ".join(c.ljust(w) for c, w in zip(row, widths, strict=True))
        for row in cells
    ]
    return "\n".join(line.rstrip() for line in lines)


def rows(items: Iterable[Mapping[str, object]], *keys: str) -> list[list[object]]:
    """The rows of a table of entries of the context, e.g. of the states.

    Args:
        items: the entries
        *keys: the keys of the columns

    Returns:
        the value of each key of each entry
    """
    return [[item[key] for key in keys] for item in items]


_FILTERS: dict[str, Callable[..., str]] = {
    "single_line": single_line,
    "python_string": python_string,
    "docstring": docstring,
    "julia_text": julia_text,
    "julia_string": julia_string,
    "r_text": r_text,
    "r_string": r_string,
}

# the functions the templates call; jinja2 types its globals narrower than a function
_GLOBALS: dict[str, Any] = {
    "wrapped": wrapped,
    "table": table,
    "rows": rows,
    "docstring": docstring,
    "julia_text": julia_text,
    "r_text": r_text,
}


@cache
def _environment(directories: tuple[Path, ...]) -> jinja2.Environment:
    """The jinja2 environment of the templates in the directories."""
    # the templates write code and documents, not html, so that html escaping would
    # corrupt the output; every text is escaped by the filters of its language
    environment = jinja2.Environment(  # noqa: S701
        loader=jinja2.FileSystemLoader([str(d) for d in directories]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )
    environment.filters.update(_FILTERS)
    environment.globals.update(_GLOBALS)
    return environment


# --- the api --------------------------------------------------------------------------


def render(system: OdeSystem, fmt: str, **options: object) -> str:
    """Render an ODE system in a format.

    Args:
        system: the ODE system
        fmt: the name of the format, a key of `FORMATS`
        **options: the options of the format, see `Format.options`

    Returns:
        the code or the document

    Raises:
        ValueError: for an unknown format, an unknown option or a value of an option
            of the wrong type
        NotImplementedError: for code of a model with a construct it does not support
    """
    format_ = _format(fmt)
    merged = _options(format_, options)
    _check_code(system, format_)
    template = _environment((TEMPLATE_DIR,)).get_template(format_.template)
    return template.render(context(system, format_, merged))


def write(
    system: OdeSystem, path: Path | str, fmt: str | None = None, **options: object
) -> Path:
    """Write an ODE system to a file, in the format of its suffix.

    Args:
        system: the ODE system
        path: the path of the file
        fmt: the name of the format, by default the format of the suffix of the path
        **options: the options of the format

    Returns:
        the path

    Raises:
        ValueError: if no format writes the suffix and no format is given, see also
            `render`
    """
    path = Path(path)
    if fmt is None:
        by_suffix = {s: f.name for f in FORMATS.values() for s in f.suffixes}
        if path.suffix not in by_suffix:
            raise ValueError(
                f"No format writes the suffix {path.suffix!r} of {path.name!r}, use "
                f"one of {sorted(by_suffix)} or name the format with `fmt`."
            )
        fmt = by_suffix[path.suffix]
    path.write_text(render(system, fmt, **options), encoding="utf-8")
    return path


def render_template(
    system: OdeSystem, template: Path | str, fmt: str = "python", **options: object
) -> str:
    """Render an ODE system with a template of its own and the context of a format.

    The template is a jinja2 template which can include the templates of
    `TEMPLATE_DIR`; it gets the context of `context` and the filters and functions
    of the templates of the formats.

    Args:
        system: the ODE system
        template: the path of the template
        fmt: the name of the format whose context and printer the template uses
        **options: the options of the format

    Returns:
        the rendered template

    Raises:
        ValueError: for an unknown format, an unknown option or a value of an option
            of the wrong type
        NotImplementedError: for a code format and a model with a construct it does
            not support
    """
    format_ = _format(fmt)
    merged = _options(format_, options)
    _check_code(system, format_)
    path = Path(template)
    environment = _environment((path.parent.absolute(), TEMPLATE_DIR))
    return environment.get_template(path.name).render(context(system, format_, merged))
