"""The formats of the ODE export: their registry, rendering context and templates.

A format is a jinja2 template in `sbmlutils/resources/converters/ode` with the math
printer of its language (`Format`, `FORMATS`). `render` checks the options against the
format, builds the names of the symbols in the format (`symbols.code_names` for code),
prints every math of the system once with the printer and renders the template with
the context of `context`: plain strings, numbers, booleans, lists and dicts, so that a
template never touches libsbml.

The context of a code format holds:

- `model`: id, name, level, version, source (the file name), units (time, substance,
  extent, volume, area, length) and `sbmlutils`, the version which writes the code;
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
- `events`: each event with `id`, `code`, `name`, `trigger` (a condition), `root`
  (its continuous root function), `initial_value`, `persistent`, `delay`,
  `priority`, `use_trigger_values` and `assignments`, each with `id`, `code`,
  `kind` (`state` or `constant`), `index`, `expr`, `scale` and `divisor_position`
  (the 0-based position in `assignments` of the assignment whose new value divides
  it, independent of `Format.first_index`, see `system.EventAssignment`);
- `scopes`: for each function of the code (`initial`, `dxdt`, `y`) what it uses:
  the `states` and `constants` it unpacks, the `assignments` it evaluates (a subset
  of `initial` or `assignments`, in their order) and whether its math uses the
  `time`; `initial` additionally holds the `computed` constants, which it writes
  into p, each with the `origin` of its initial value (`initial_assignment` or
  `initial_value`, a conversion with another quantity);
- `modules`: the modules of the language the printed math uses, of
  `MathPrinter.MODULES`, e.g. `math`;
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
from sbmlutils.converters.ode.printers import PRINTERS, MathPrinter
from sbmlutils.converters.ode.symbols import code_names
from sbmlutils.converters.ode.text import single_line

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
        """The context."""
        system = self.system
        info = system.info
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
        events = [self.event(k, by_id) for k in range(len(system.events))]
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
            },
            "states": states,
            "constants": constants,
            "assigned": assigned,
            "functions": functions,
            "initial": initial,
            "assignments": assignments,
            "odes": odes,
            "events": events,
            "scopes": self.scopes(states, constants, initial, assignments),
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
                    "expr": self.expr(a.math),
                    "scale": self.expr(a.scale),
                    "divisor_position": None
                    if a.divisor is None
                    else variables.index(a.divisor),
                }
            )
        symbol = event.symbol
        return {
            "id": symbol.sid,
            "code": self.codes[symbol.sid],
            "name": single_line(symbol.name) if symbol.name else None,
            "trigger": self.expr(event.trigger, condition=True),
            "root": self.expr(event.root),
            "initial_value": event.initial_value,
            "persistent": event.persistent,
            "delay": self.expr(event.delay),
            "priority": self.expr(event.priority),
            "use_trigger_values": event.use_values_from_trigger_time,
            "assignments": assignments,
        }

    def scopes(
        self,
        states: Sequence[dict[str, object]],
        constants: Sequence[dict[str, object]],
        initial: Sequence[dict[str, object]],
        assignments: Sequence[dict[str, object]],
    ) -> dict[str, dict[str, object]]:
        """What each function of the code uses, so that it computes nothing unused."""
        system = self.system

        def scope(
            used: set[str],
            evaluated: Sequence[dict[str, object]],
            time: bool,
            computed: Mapping[str, str] | None = None,
        ) -> dict[str, object]:
            computed = computed or {}
            computed_ids = {str(a["id"]) for a in evaluated}
            return {
                "states": [x for x in states if x["id"] in used - computed_ids],
                "constants": [c for c in constants if c["id"] in used - computed_ids],
                "assignments": [a for a in evaluated if a["id"] in used],
                "time": time,
                "computed": [
                    {**c, "origin": computed[str(c["id"])]}
                    for c in constants
                    if c["id"] in computed
                ],
            }

        # the initial values: the states and the constants they set, and what these use
        maths = {a.variable: a.math for a in system.initial}
        computed = {
            a.variable: a.origin
            for a in system.initial
            if a.variable in system.constants
        }
        used = _needed([*system.states, *computed], maths)
        time = any(_uses_time(a.math) for a in system.initial if a.variable in used)
        initial_scope = scope(used, initial, time, computed)

        # the rates of change: the odes and the assignments they use
        maths = {a.variable: a.math for a in system.assignments}
        used = _needed(set().union(*(names(o.rhs) for o in system.odes)), maths)
        time = any(_uses_time(o.rhs) for o in system.odes) or any(
            _uses_time(a.math) for a in system.assignments if a.variable in used
        )
        dxdt = scope(used, assignments, time)

        # the assigned values: every assignment
        used = _needed(system.assigned, maths)
        y = scope(
            used, assignments, any(_uses_time(a.math) for a in system.assignments)
        )
        return {"initial": initial_scope, "dxdt": dxdt, "y": y}

    def modules(self) -> list[str]:
        """The modules of the printer the printed math uses, e.g. `np` and `math`."""
        return sorted(
            module
            for module in self.printer.MODULES
            if any(
                re.search(rf"(?<![\w.]){re.escape(module)}\.", code)
                for code in self.printed
            )
        )


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
        NotImplementedError: for a document format, whose context is not written yet
    """
    if fmt.kind != "code":
        raise NotImplementedError(
            f"The context of the {fmt.name} format is not written."
        )
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


def wrapped(
    items: Sequence[object], indent: int, column: int, tail: int = 1, width: int = 88
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

    Returns:
        the list from its opening to its closing bracket
    """
    texts = [str(item) for item in items]
    single = f"[{', '.join(texts)}]"
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
    lines.append(line)
    body = "\n".join(inner + line for line in lines)
    return f"[\n{body}\n{' ' * indent}]"


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
}

# the functions the templates call; jinja2 types its globals narrower than a function
_GLOBALS: dict[str, Any] = {
    "wrapped": wrapped,
    "table": table,
    "rows": rows,
    "docstring": docstring,
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
    if format_.kind == "code" and system.events:
        listed = ", ".join(f"event {e.symbol.sid!r}" for e in system.events)
        raise NotImplementedError(
            f"The {format_.name} code does not support events yet: {listed}."
        )
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
    of the templates of the formats. Unlike `render`, it renders a model with events:
    the events are in the context, a template of its own may handle them.

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
