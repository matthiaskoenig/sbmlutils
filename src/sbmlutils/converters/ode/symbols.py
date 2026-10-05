"""Names of the symbols of a model per output format.

The ids of a model are SIds: ASCII letters, digits and underscores, not starting with a
digit. They are written in two ways:

- as the identifier of a variable in python, julia and R, where an id which is a
  keyword, a builtin or a name the generated code uses itself must not be taken
  (`code_names`),
- as a typeset math symbol in LaTeX and typst, where the id is split into a base and a
  subscript, `k_cat_glc` is `k` with the subscript `cat_glc` (`typeset_symbol`,
  `typeset_names`).
"""

import builtins
import keyword
import re
from collections.abc import Iterable, Mapping
from typing import Literal

from sbmlutils.converters.ode.printers import JuliaPrinter, PythonPrinter, RPrinter
from sbmlutils.converters.ode.printers.base import MathPrinter
from sbmlutils.converters.ode.text import check_sid

__all__ = ["RESERVED", "code_names", "typeset_names", "typeset_symbol"]

Dialect = Literal["latex", "typst"]

# --- the names of the code --------------------------------------------------------------

# The modules of the dialect tables: `np.abs` reserves the module `np` and the member
# `abs`, the member being a name which an id could shadow in a language where it is
# called without the module.
_MODULES = PythonPrinter.MODULES | JuliaPrinter.MODULES | RPrinter.MODULES

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")
_NUMBER = re.compile(r"(?<![A-Za-z0-9_])\d+\.?\d*(?:[eE][+-]?\d+)?")


def _written(printer: type[MathPrinter]) -> set[str]:
    """The names a printer writes through its dialect tables.

    The tables map the functions and constants of SBML to the code which is written, e.g.
    `np.sin`, `NaNMath.cos`, `exp(1.0)`; the code is split into its identifiers, and a
    name of a module is split into the module and the member.

    Args:
        printer: the printer class of a dialect

    Returns:
        the identifiers of the tables
    """
    names: set[str] = set()
    for table in (
        printer.FUNCTIONS,
        printer.CONSTANTS,
        printer.RECIPROCALS,
        printer.OF_RECIPROCALS,
    ):
        for code in table.values():
            for name in _IDENTIFIER.findall(_NUMBER.sub("", code)):
                module, _, member = name.partition(".")
                names.update([module, member] if module in _MODULES else [name])
    names.discard("")
    return names


# The names the methods of the printers write beside their tables (`call("np.fmod", ...)`
# in `rem`, `quotient`, `log`, `root`, the logic and the conditions), a module and its
# members as separate names. `tests/converters/ode/test_ode_symbols.py` prints the formulas of the
# printer tests and checks that every name of the output is reserved, so that a name
# added to a printer without being listed here is found.
_PRINTED: dict[str, set[str]] = {
    "python": {
        "np",
        "math",
        "nan",
        "inf",
        "fmod",
        "trunc",
        "log10",
        "sqrt",
        "gamma",
        "bool",
        "float",
    },
    "julia": {
        "NaNMath",
        "pow",
        "log10",
        "sqrt",
        "rem",
        "trunc",
        "xor",
        "gamma",
        "Float64",
    },
    "r": {
        "abs",
        "sign",
        "trunc",
        "log10",
        "log",
        "sqrt",
        "xor",
        "isTRUE",
        "as.numeric",
        "gamma",
    },
}

# The names the generated code uses itself: the arguments `t`, `x`, `p`, `dx`, `y`, the
# initial values `x0`, `p0`, the functions of the file and the packages it uses. The
# names which are built from an id (`v_<reaction id>`, `event_assign_<id>`) are not
# listed, they are made unique by the generator which builds them.
_GENERATED: dict[str, set[str]] = {
    # the names of `resources/converters/ode/python.py.jinja`: the module, its
    # functions, their arguments and locals
    "python": {
        "t", "x", "p", "dx", "y", "x0", "p0",
        "np", "pd", "math", "scipy", "solve_ivp",
        "XIDS", "PIDS", "YIDS", "NAMES", "UNITS", "P0", "EVENTS",
        "f_dxdt", "f_y", "initial_values", "simulate", "event_triggers",
        "t_end", "points", "rtol", "atol", "method", "x_initial", "times",
        "solution", "xt", "yt", "data",
        "xids", "pids", "yids",
        # the events
        "event_conditions", "execute_events", "first_change", "DenseOutput",
        "partial", "values", "interpolant", "t_old", "t_new", "t_low", "t_high",
        "t_middle", "changed", "turned", "holds", "holds_now", "event_index",
        "event", "delay_time", "pending", "due", "scheduled", "ranks",
        "priority_value", "execution", "t_next", "t_stop", "max_step", "solver",
        "solver_type", "rows", "pt", "columns", "MAX_STEPS", "MAX_CASCADE",
        "max_steps", "steps", "step_size", "executions",
    },
    "julia": {
        "t", "x", "p", "dx", "y", "x0", "p0",
        "NaNMath", "SpecialFunctions", "DifferentialEquations", "DataFrames",
        "solve", "ODEProblem", "Rodas5P", "VectorContinuousCallback",
        "f_dxdt", "f_y", "initial_values", "simulate", "event_triggers",
        "xids", "pids", "yids",
    },
    "r": {
        "t", "x", "p", "dx", "y", "x0", "p0",
        "deSolve", "lsoda",
        "f_dxdt", "f_y", "initial_values", "simulate", "event_triggers",
        "xids", "pids", "yids",
    },
}  # fmt: skip

# Python: the keywords, the soft keywords (`match`, `case`, `type`, `_`), the public
# builtins and the dunder names of a module. The private names of the builtins are
# not taken from the interpreter: an extension module may add one at runtime (pybind11
# adds `__pybind11_internals_v4_...__`), which would make the names depend on what was
# imported before this module.
_PYTHON = (
    set(keyword.kwlist)
    | set(keyword.softkwlist)
    | {name for name in dir(builtins) if not name.startswith("_")}
    | {
        "__import__", "__build_class__", "__debug__", "__name__", "__doc__",
        "__file__", "__main__", "__builtins__", "__spec__", "__loader__",
        "__package__", "__annotations__", "__dict__", "__all__",
    }
)  # fmt: skip

# Julia: the keywords of the language (https://docs.julialang.org/en/v1/base/base/#Keywords)
# and the names of `Base` which the generated code or a reader would call, the constants
# `Inf`, `NaN`, `pi`, `e` (of `MathConstants`) and the types.
_JULIA = {
    # keywords
    "baremodule", "begin", "break", "catch", "const", "continue", "do", "else",
    "elseif", "end", "export", "false", "finally", "for", "function", "global", "if",
    "import", "let", "local", "macro", "module", "quote", "return", "struct", "true",
    "try", "using", "while", "abstract", "mutable", "primitive", "type", "in", "isa",
    "where",
    # constants and types
    "Inf", "NaN", "pi", "e", "im", "nothing", "missing", "undef", "Inf64", "NaN64",
    "Float64", "Float32", "Int", "Int64", "Bool", "String", "Symbol", "Number", "Real",
    "Any", "Vector", "Matrix", "Array", "Dict", "Tuple", "Set", "Nothing", "Missing",
    "Base", "Core", "Main",
    # functions of `Base`
    "abs", "abs2", "acos", "acosh", "asin", "asinh", "atan", "atanh", "ceil", "cos",
    "cosh", "exp", "expm1", "floor", "log", "log10", "log1p", "log2", "max", "min",
    "sin", "sinh", "sqrt", "tan", "tanh", "sign", "rem", "mod", "div", "fld", "cld",
    "trunc", "round", "gamma", "xor", "ifelse", "isnan", "isinf", "isfinite", "zeros",
    "ones", "fill", "length", "size", "sum", "prod", "map", "filter", "reduce", "push!",
    "print", "println", "show", "string", "float", "convert", "big", "eps", "identity",
    "typeof", "error", "throw", "first", "last", "range", "collect", "copy", "similar",
    "vcat", "hcat", "reshape", "findfirst", "any", "all", "count", "sort", "unique",
}  # fmt: skip

# R: the reserved words (`?Reserved`) and the names of base R which the generated code or
# a reader would use, `T` and `F` which are variables holding `TRUE` and `FALSE`, `c`,
# `t` (transpose), `pi`, `list`, `rep`, `sum`.
_R = {
    # reserved words
    "if", "else", "repeat", "while", "function", "for", "next", "break", "TRUE",
    "FALSE", "NULL", "Inf", "NaN", "NA", "NA_integer_", "NA_real_", "NA_character_",
    "NA_complex_", "in",
    # names of base R
    "T", "F", "c", "list", "pi", "rep", "seq", "seq_len", "seq_along", "sum", "prod",
    "length", "names", "numeric", "character", "logical", "vector", "matrix", "array",
    "data.frame", "return", "stop", "warning", "print", "cat", "paste", "paste0",
    "sapply", "lapply", "vapply", "mapply", "Reduce", "Filter", "Map", "ifelse", "is.na",
    "is.nan", "is.finite", "is.infinite", "isTRUE", "isFALSE", "identical", "all", "any",
    "which", "rev", "sort", "order", "unique", "min", "max", "abs", "sqrt", "exp", "log",
    "log10", "log2", "sin", "cos", "tan", "sinh", "cosh", "tanh", "asin", "acos", "atan",
    "asinh", "acosh", "atanh", "floor", "ceiling", "round", "trunc", "sign", "gamma",
    "xor", "as.numeric", "as.integer", "as.logical", "as.character", "unlist", "setNames",
    "with", "within", "local", "mean", "median", "var", "sd", "range", "diff", "cumsum",
    "rbind", "cbind", "dim", "nrow", "ncol", "apply", "t", "q", "D", "I", "pmin", "pmax",
    "nchar", "substr", "library", "require", "source", "invisible", "tryCatch", "try",
    "switch", "Recall", "environment", "new.env", "assign", "get", "exists",
}  # fmt: skip

RESERVED: dict[str, frozenset[str]] = {
    "python": frozenset(
        _PYTHON | _written(PythonPrinter) | _PRINTED["python"] | _GENERATED["python"]
    ),
    "julia": frozenset(
        _JULIA | _written(JuliaPrinter) | _PRINTED["julia"] | _GENERATED["julia"]
    ),
    "r": frozenset(_R | _written(RPrinter) | _PRINTED["r"] | _GENERATED["r"]),
}
"""The names which an id must not take in the code of a language.

The keywords and builtins of the language, the functions and constants the printer of
the language writes, and the names the generated code uses itself.
"""

_SID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*", re.ASCII)


def _is_valid(name: str, language: str) -> bool:
    """Whether a name is an identifier of the language.

    Args:
        name: the SId
        language: python, julia or r

    Returns:
        `False` for the SId which starts with an underscore in R only
    """
    return not (language == "r" and name.startswith("_"))


def code_names(ids: Iterable[str], language: str) -> dict[str, str]:
    """The name of every id as a variable of the generated code of a language.

    An id is its own name, except for an id which is reserved in the language (a keyword,
    a builtin, a name the code or the printer uses), and an id which R cannot write
    (`_x` starts with an underscore): such an id gets underscores appended (and `x`
    prepended in R for the leading underscore) until its name is neither reserved nor the
    name of another id. The ids which are not renamed keep their name, the others are
    named in the order of the input, so that the result is deterministic.

    Args:
        ids: the ids of the model
        language: `"python"`, `"julia"` or `"r"`

    Returns:
        the name of every id, in the order of the ids

    Raises:
        ValueError: if the language is unknown or an id is not an SId
    """
    if language not in RESERVED:
        raise ValueError(
            f"No code names for {language!r}, use one of {sorted(RESERVED)}."
        )
    reserved = RESERVED[language]
    sids = list(dict.fromkeys(check_sid(sid) for sid in ids))
    taken = set(reserved) | set(sids)
    names: dict[str, str] = {}
    pending: list[str] = []
    for sid in sids:
        if sid in reserved or not _is_valid(sid, language):
            pending.append(sid)
        names[sid] = sid
    for sid in pending:
        name = sid if _is_valid(sid, language) else f"x{sid}"
        while name in taken:
            name += "_"
        taken.add(name)
        names[sid] = name
    return names


# --- the symbols of the documents ---------------------------------------------------------


def _typeset(sid: str, dialect: Dialect) -> str:
    """The symbol of a valid id, see `typeset_symbol`."""
    latex = dialect == "latex"

    def text(value: str) -> str:
        """Upright text, a string in typst and a mathrm in LaTeX."""
        if latex:
            escaped = value.replace("_", r"\_")
            return rf"\mathrm{{{escaped}}}"
        return f'upright("{value}")'

    base, separator, sub = sid.partition("_")
    if not base or (separator and not sub):
        # `_x` has no base, `x_` no subscript: the id is text, with its underscores
        return text(sid)
    symbol = base if len(base) == 1 else text(base)
    if not separator:
        return symbol
    if sub.isdigit():
        content = sub
    elif latex:
        content = text(sub)
    else:
        # a string is a subscript on its own, `k_("cat_glc")`, upright already
        content = f'"{sub}"'
    return f"{symbol}_{{{content}}}" if latex else f"{symbol}_({content})"


def typeset_symbol(sid: str, dialect: Dialect) -> str:
    r"""The math symbol of an id.

    The part before the first underscore is the base, the rest is the subscript:
    `k_cat_glc` is `k` with the subscript `cat_glc`. A base of one letter is italic, a
    base of more letters is upright text, `Glc` is `\mathrm{Glc}` (`upright("Glc")` in
    typst). A subscript is upright text with its underscores, `k_{\mathrm{cat\_glc}}`
    (`k_("cat_glc")`), except a subscript of digits only, which is a number,
    `k_{1}` (`k_(1)`). An id without a base (`_x`) or without a subscript (`x_`) is
    upright text as a whole, `\mathrm{\_x}` (`upright("_x")`).

    The id is an SId, so the text holds letters, digits and underscores only and needs no
    escaping but the underscore in LaTeX.

    Args:
        sid: the id
        dialect: `"latex"` or `"typst"`

    Returns:
        the math of the symbol

    Raises:
        ValueError: if the id is not an SId or the dialect is unknown
    """
    if dialect not in ("latex", "typst"):
        raise ValueError(f"No symbols for {dialect!r}, use latex or typst.")
    if not _SID.fullmatch(sid):
        raise ValueError(f"The id {sid!r} is not an SId and cannot be typeset.")
    return _typeset(sid, dialect)


_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*", re.ASCII)


def typeset_names(
    ids: Iterable[str], dialect: Dialect, names: Mapping[str, str] | None = None
) -> dict[str, str]:
    """The math symbol of every id, of its name if it has one which is a valid symbol.

    With `names` the symbol of an element is made of its name if the name starts with a
    letter and holds letters, digits and underscores only, else of its id. Two elements
    are never written with the same symbol, a reader could not tell them apart: an
    element whose name gives the symbol of another element falls back to its id, until
    no two symbols are equal.

    Args:
        ids: the ids of the elements
        dialect: `"latex"` or `"typst"`
        names: the name of an element by its id, the elements without a name or with
            a name which is no symbol are written with their id

    Returns:
        the symbol of every id, in the order of the ids

    Raises:
        ValueError: if an id is not an SId or the dialect is unknown
    """
    sids = list(dict.fromkeys(ids))
    by_id = {sid: typeset_symbol(sid, dialect) for sid in sids}
    chosen = dict(by_id)
    named: set[str] = set()
    for sid in sids:
        name = (names or {}).get(sid)
        if name is not None and _NAME.fullmatch(name):
            chosen[sid] = typeset_symbol(name, dialect)
            named.add(sid)
    while True:
        count: dict[str, int] = {}
        for symbol in chosen.values():
            count[symbol] = count.get(symbol, 0) + 1
        clashing = {sid for sid in named if count[chosen[sid]] > 1}
        if not clashing:
            return chosen
        for sid in clashing:
            chosen[sid] = by_id[sid]
        named -= clashing
