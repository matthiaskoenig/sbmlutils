"""Test the names of the symbols per output format of the ODE export."""

import keyword
import re
from pathlib import Path
from typing import Literal

import libsbml
import pytest
from ode_helpers import FORMULAS, compile_typst

from sbmlutils.converters.ode.printers import PRINTERS
from sbmlutils.converters.ode.symbols import (
    RESERVED,
    code_names,
    typeset_names,
    typeset_symbol,
)

# --- code names -----------------------------------------------------------------------


def test_reserved_ids_are_renamed() -> None:
    """A reserved id gets underscores until it is unique, an existing id keeps its name."""
    assert code_names(["lambda", "t", "lambda_"], "python") == {
        "lambda": "lambda__",
        "t": "t_",
        "lambda_": "lambda_",
    }


@pytest.mark.parametrize(
    ("language", "sid", "expected"),
    [
        ("python", "lambda", "lambda_"),
        ("python", "None", "None_"),
        ("python", "print", "print_"),
        ("python", "np", "np_"),
        ("python", "math", "math_"),
        ("python", "__name__", "__name___"),
        ("python", "match", "match_"),
        ("python", "x", "x_"),
        ("python", "dx", "dx_"),
        ("julia", "end", "end_"),
        ("julia", "function", "function_"),
        ("julia", "NaNMath", "NaNMath_"),
        ("julia", "Inf", "Inf_"),
        ("julia", "pi", "pi_"),
        ("julia", "gamma", "gamma_"),
        ("julia", "rem", "rem_"),
        ("julia", "trunc", "trunc_"),
        ("r", "T", "T_"),
        ("r", "F", "F_"),
        ("r", "c", "c_"),
        ("r", "if", "if_"),
        ("r", "isTRUE", "isTRUE_"),
        ("r", "sign", "sign_"),
        ("r", "gamma", "gamma_"),
        ("r", "NA", "NA_"),
        ("r", "list", "list_"),
        ("r", "lsoda", "lsoda_"),
        ("r", "deSolve", "deSolve_"),
        ("r", "simulate", "simulate_"),
        ("r", "repeat", "repeat_"),
    ],
)
def test_reserved_names(language: str, sid: str, expected: str) -> None:
    """The names of the language and of the generated code are not used as ids."""
    assert code_names([sid], language) == {sid: expected}


def test_names_of_one_language_are_not_reserved_in_another() -> None:
    """`end` is a keyword of julia only, `T` a name of R only, `lambda` of python only."""
    assert code_names(["end", "T", "lambda"], "python") == {
        "end": "end",
        "T": "T",
        "lambda": "lambda_",
    }
    assert code_names(["end", "T", "lambda"], "julia") == {
        "end": "end_",
        "T": "T",
        "lambda": "lambda",
    }
    assert code_names(["end", "T", "lambda"], "r") == {
        "end": "end",
        "T": "T_",
        "lambda": "lambda",
    }


def test_code_names_identity() -> None:
    """An id which is neither reserved nor a clash is written as it is."""
    sids = ["Glc", "k_cat", "_x", "A1", "v_r1"]
    assert code_names(sids, "python") == {sid: sid for sid in sids}
    assert code_names(sids, "julia") == {sid: sid for sid in sids}


def test_code_names_are_deterministic_in_input_order() -> None:
    """Two reserved ids which collide after the rename are renamed in input order."""
    # `t_` is a free name, so `t` takes it, and `t__` is the next free one
    assert code_names(["t", "t_"], "python") == {"t": "t__", "t_": "t_"}
    assert code_names(["t_", "t"], "python") == {"t_": "t_", "t": "t__"}
    # `x_` is taken by an id, `x__` by the renamed `x`, so `dx` must end up elsewhere
    names = code_names(["x", "x_", "dx", "dx_"], "python")
    assert names == {"x": "x__", "x_": "x_", "dx": "dx__", "dx_": "dx_"}
    assert len(set(names.values())) == len(names)


def test_code_names_are_unique_and_not_reserved() -> None:
    """No name is reserved and no two ids share a name."""
    for language, reserved in RESERVED.items():
        sids = sorted(reserved) + [f"{sid}_" for sid in sorted(reserved)]
        sids = [sid for sid in sids if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", sid)]
        names = code_names(sids, language)
        assert list(names) == sids
        assert len(set(names.values())) == len(sids), language
        assert not set(names.values()) & reserved, language


def test_code_names_of_duplicate_ids() -> None:
    """An id which is given twice is named once."""
    assert code_names(["t", "t"], "python") == {"t": "t_"}


def test_r_has_no_name_which_starts_with_underscore() -> None:
    """`_x` is a valid SId, but a syntax error in R."""
    assert code_names(["_x", "_", "x_x"], "r") == {
        "_x": "x_x_",
        "_": "x_",
        "x_x": "x_x",
    }
    assert code_names(["_x"], "python") == {"_x": "_x"}
    assert code_names(["_x"], "julia") == {"_x": "_x"}


def test_julia_special_forms_are_reserved() -> None:
    """The special forms and the functions of every module of julia are reserved.

    `ccall` and `cglobal` cannot be assigned, `eval` and `include` are defined by
    every module.
    """
    names = code_names(["ccall", "cglobal", "eval", "include"], "julia")
    assert names == {n: f"{n}_" for n in ["ccall", "cglobal", "eval", "include"]}


def test_julia_has_no_name_of_underscores_only() -> None:
    """`_` and `__` are valid SIds, but julia can assign them, never read them."""
    assert code_names(["_", "__", "_x"], "julia") == {
        "_": "x_",
        "__": "x__",
        "_x": "_x",
    }
    # the name is unique against the other ids
    assert code_names(["_", "x_"], "julia") == {"_": "x__", "x_": "x_"}


def test_unknown_language_raises() -> None:
    """Only python, julia and R have code names."""
    with pytest.raises(ValueError, match="matlab"):
        code_names(["x"], "matlab")


def test_python_keywords_and_builtins_are_reserved() -> None:
    """Every keyword and builtin of python is reserved."""
    import builtins

    assert set(keyword.kwlist) <= RESERVED["python"]
    # an extension module may add a private name to the builtins at runtime, after
    # `RESERVED` was built, e.g. `__pybind11_internals_v4_...__` once scipy is imported
    public = {name for name in dir(builtins) if not name.startswith("_")}
    assert public <= RESERVED["python"]
    assert {"__import__", "__build_class__", "__debug__", "__name__"} <= RESERVED[
        "python"
    ]


IDENTIFIER = re.compile(r"(?<![A-Za-z0-9_.])[A-Za-z_][A-Za-z0-9_.]*")
NUMBER = re.compile(r"(?<![A-Za-z0-9_])\d+\.?\d*(?:[eE][+-]?\d+)?")
FORMULA_SYMBOLS = {"A": "A", "k": "k", "f": "f"}
MODULES = {"np", "NaNMath", "math"}


def _parts(name: str) -> list[str]:
    """The names a written name reserves: `np.abs` is the module and the member."""
    module, _, member = name.partition(".")
    return [module, member] if module in MODULES else [name]


@pytest.mark.parametrize("language", ["python", "julia", "r"])
def test_every_name_of_the_dialect_is_reserved(language: str) -> None:
    """Every function, constant and module the printer writes is reserved.

    The printer prints the formulas of the printer tests (all node types and
    functions), and every name of the output, which is not a symbol, is reserved:
    an id of the model must never shadow a name which the printer writes.
    """
    printer = PRINTERS[language]()
    found: set[str] = set()
    for formula in [*FORMULAS, "factorial(A)", "log(3, A) + A != k"]:
        math = libsbml.parseL3Formula(formula)
        assert math is not None
        code = NUMBER.sub("", printer.print(math, FORMULA_SYMBOLS))
        found.update(IDENTIFIER.findall(code))
    found -= set(FORMULA_SYMBOLS)
    assert found
    for name in found:
        assert set(_parts(name)) <= RESERVED[language], name
    # the tables of the printer, which hold names the formulas may not reach
    for table in (
        printer.FUNCTIONS,
        printer.CONSTANTS,
        printer.RECIPROCALS,
        printer.OF_RECIPROCALS,
    ):
        for code in table.values():
            for name in IDENTIFIER.findall(NUMBER.sub("", code)):
                assert set(_parts(name)) <= RESERVED[language], name


@pytest.mark.parametrize(
    ("language", "names"),
    [
        ("python", ["t", "x", "p", "dx", "y", "x0", "p0", "np", "math", "pd", "scipy"]),
        (
            "julia",
            ["t", "x", "p", "dx", "y", "x0", "p0", "NaNMath", "SpecialFunctions"],
        ),
        ("r", ["t", "x", "p", "dx", "y", "x0", "p0", "pi", "rep", "sum", "function"]),
    ],
)
def test_names_of_generated_code_are_reserved(language: str, names: list[str]) -> None:
    """The names the generated code uses itself are reserved."""
    assert set(names) <= RESERVED[language]


# --- typeset symbols ------------------------------------------------------------------

SYMBOLS = [
    # (sid, latex, typst)
    ("A", "A", "A"),
    ("k", "k", "k"),
    ("Glc", r"\mathrm{Glc}", 'upright("Glc")'),
    ("k_cat_glc", r"k_{\mathrm{cat\_glc}}", 'k_("cat_glc")'),
    ("k_cat", r"k_{\mathrm{cat}}", 'k_("cat")'),
    ("Vmax_glc", r"\mathrm{Vmax}_{\mathrm{glc}}", 'upright("Vmax")_("glc")'),
    # a subscript of digits only is a number, no text
    ("k_1", "k_{1}", "k_(1)"),
    ("k_12", "k_{12}", "k_(12)"),
    # digits and letters mixed are text
    ("k_1a", r"k_{\mathrm{1a}}", 'k_("1a")'),
    # letters followed by digits only have the digits as subscript
    ("k1", "k_{1}", "k_(1)"),
    ("S0", "S_{0}", "S_(0)"),
    ("Km2", r"\mathrm{Km}_{2}", 'upright("Km")_(2)'),
    ("alpha12", r"\alpha_{12}", "alpha_(12)"),
    ("k1a", r"\mathrm{k1a}", 'upright("k1a")'),
    ("a0_tr", r"\mathrm{a0}_{\mathrm{tr}}", 'upright("a0")_("tr")'),
    ("v_r1", r"v_{\mathrm{r1}}", 'v_("r1")'),
    # a subscript of one letter is text as well
    ("v_r", r"v_{\mathrm{r}}", 'v_("r")'),
    # an id which starts or ends with an underscore has no base or no subscript, it is
    # written as text, whole
    ("_x", r"\mathrm{\_x}", 'upright("_x")'),
    ("__", r"\mathrm{\_\_}", 'upright("__")'),
    ("x_", r"\mathrm{x\_}", 'upright("x_")'),
    ("_", r"\mathrm{\_}", 'upright("_")'),
    ("_1", r"\mathrm{\_1}", 'upright("_1")'),
    # a base which is the name of a Greek letter is the letter, the subscript is not
    ("alpha", r"\alpha", "alpha"),
    ("beta0", r"\beta_{0}", "beta_(0)"),
    ("tau_mRNA", r"\tau_{\mathrm{mRNA}}", 'tau_("mRNA")'),
    ("k_alpha", r"k_{\mathrm{alpha}}", 'k_("alpha")'),
    ("pi", r"\pi", "pi"),
    ("epsilon", r"\varepsilon", "epsilon"),
    ("phi_x", r"\varphi_{\mathrm{x}}", 'phi_("x")'),
    ("Gamma", r"\Gamma", "Gamma"),
    ("Omega_1", r"\Omega_{1}", "Omega_(1)"),
    # omicron is the Latin o, an upper case letter which is a Latin one stays text
    ("omicron", "o", "o"),
    ("Alpha", r"\mathrm{Alpha}", 'upright("Alpha")'),
    ("Tau_x", r"\mathrm{Tau}_{\mathrm{x}}", 'upright("Tau")_("x")'),
    # a name which only starts like a Greek letter is no Greek letter
    ("alphas", r"\mathrm{alphas}", 'upright("alphas")'),
    # the underscores after the first are part of the subscript
    ("a__b", r"a_{\mathrm{\_b}}", 'a_("_b")'),
    ("a_b_", r"a_{\mathrm{b\_}}", 'a_("b_")'),
]


@pytest.mark.parametrize(("sid", "latex", "typst"), SYMBOLS)
def test_typeset_symbol(sid: str, latex: str, typst: str) -> None:
    """The base is the part before the first underscore, the rest the subscript."""
    assert typeset_symbol(sid, "latex") == latex
    assert typeset_symbol(sid, "typst") == typst


@pytest.mark.parametrize(
    "sid", ["", "a b", "1a", "a-b", 'a"b', "a\\b", "a}", "é", "a$"]
)
@pytest.mark.parametrize("dialect", ["latex", "typst"])
def test_typeset_symbol_rejects_what_is_no_sid(sid: str, dialect: str) -> None:
    """Only an SId is typeset, so that no id can write markup."""
    with pytest.raises(ValueError, match="SId"):
        typeset_symbol(sid, dialect)  # ty: ignore[invalid-argument-type]


def test_typeset_symbol_unknown_dialect() -> None:
    """The dialects are latex and typst."""
    with pytest.raises(ValueError, match="markdown"):
        typeset_symbol("A", "markdown")  # ty: ignore[invalid-argument-type]


def test_typst_symbols_compile(tmp_path: Path) -> None:
    """Every typst symbol compiles, in a sum, a power and a fraction."""
    body = "\n".join(
        f"$ {symbol} + {symbol}^2 + ({symbol})/({symbol}) $" for _, _, symbol in SYMBOLS
    )
    pdf = compile_typst(body, tmp_path)
    assert pdf.startswith(b"%PDF")


def test_typst_symbols_render_as_the_symbol(tmp_path: Path) -> None:
    """The typst symbols are not read as a function, a unit or a builtin."""
    typst = pytest.importorskip("typst")
    for sid in [
        "pi",
        "sin",
        "cos",
        "alpha",
        "Glc",
        "e",
        "i",
        "inf",
        "k_pi",
        "oo_x",
        "eta",
    ]:
        source = f"$ {typeset_symbol(sid, 'typst')} $"
        path = tmp_path / "symbol.typ"
        path.write_text(source)
        _, warnings = typst.compile_with_warnings(str(path))
        assert not warnings, sid
    # a multi letter base is a string, so that `sin` is no function, `inf` no symbol;
    # the name of a Greek letter is the letter
    assert typeset_symbol("sin_x", "typst") == 'upright("sin")_("x")'
    assert typeset_symbol("inf", "typst") == 'upright("inf")'
    assert typeset_symbol("pi", "typst") == "pi"


# --- typeset names --------------------------------------------------------------------


@pytest.mark.parametrize("dialect", ["latex", "typst"])
def test_typeset_names_of_ids(dialect: str) -> None:
    """Without names every id is typeset."""
    sids = ["A", "k_cat", "Glc"]
    assert typeset_names(sids, dialect) == {  # ty: ignore[invalid-argument-type]
        sid: typeset_symbol(sid, dialect)  # ty: ignore[invalid-argument-type]
        for sid in sids
    }


def test_typeset_names_use_the_name() -> None:
    """A name which is a valid symbol is typeset instead of the id."""
    names = {
        "s1": "Glc",
        "s2": "G6P_ext",
        "s3": "glucose 6-phosphate",
        "s4": "",
        "s5": "1x",
    }
    assert typeset_names(["s1", "s2", "s3", "s4", "s5", "s6"], "latex", names) == {
        "s1": r"\mathrm{Glc}",
        "s2": r"\mathrm{G6P}_{\mathrm{ext}}",
        "s3": "s_{3}",
        "s4": "s_{4}",
        "s5": "s_{5}",
        "s6": "s_{6}",
    }
    assert typeset_names(["s1", "s2", "s3"], "typst", names) == {
        "s1": 'upright("Glc")',
        "s2": 'upright("G6P")_("ext")',
        "s3": "s_(3)",
    }


def test_typeset_names_start_with_a_letter() -> None:
    """A name which starts with an underscore falls back to the id."""
    assert typeset_names(["s1"], "latex", {"s1": "_x"}) == {"s1": "s_{1}"}


def test_typeset_names_are_unique() -> None:
    """Two elements are never typeset the same: a clash falls back to the ids."""
    names = {"s1": "Glc", "s2": "Glc", "s3": "s4", "s5": "k", "s6": "s7", "s7": "s6"}
    sids = ["s1", "s2", "s3", "s4", "s5", "k", "s6", "s7"]
    result = typeset_names(sids, "typst", names)
    # `s1` and `s2` share a name, `s3` is named like the id of `s4`, `s5` like `k`
    assert result["s1"] == "s_(1)"
    assert result["s2"] == "s_(2)"
    assert result["s3"] == "s_(3)"
    assert result["s4"] == "s_(4)"
    assert result["s5"] == "s_(5)"
    assert result["k"] == "k"
    # a swap of names is no clash
    assert result["s6"] == "s_(7)"
    assert result["s7"] == "s_(6)"
    assert len(set(result.values())) == len(result)


@pytest.mark.parametrize("dialect", ["latex", "typst"])
def test_typeset_names_of_numbered_ids_are_unique(
    dialect: Literal["latex", "typst"],
) -> None:
    """`k1` and `k_1` are both `k_1`: the id of letters and digits is upright text."""
    result = typeset_names(["k1", "k_1", "S0"], dialect)
    expected = {
        "latex": {"k1": r"\mathrm{k1}", "k_1": "k_{1}", "S0": "S_{0}"},
        "typst": {"k1": 'upright("k1")', "k_1": "k_(1)", "S0": "S_(0)"},
    }
    assert result == expected[dialect]


@pytest.mark.parametrize("dialect", ["latex", "typst"])
def test_typeset_names_of_greek_ids_are_unique(
    dialect: Literal["latex", "typst"],
) -> None:
    """A Greek letter typeset like another id is its name, numbered ids are text."""
    result = typeset_names(["o", "omicron", "alpha0", "alpha_0", "tau"], dialect)
    expected = {
        "latex": {
            "o": "o",
            "omicron": r"\mathrm{omicron}",
            "alpha0": r"\mathrm{alpha0}",
            "alpha_0": r"\alpha_{0}",
            "tau": r"\tau",
        },
        "typst": {
            "o": "o",
            "omicron": 'upright("omicron")',
            "alpha0": 'upright("alpha0")',
            "alpha_0": "alpha_(0)",
            "tau": "tau",
        },
    }
    assert result == expected[dialect]


def test_typeset_names_of_greek_names() -> None:
    """A name which is the name of a Greek letter is the letter."""
    names = {"k1": "lambda", "k2": "Omega_max"}
    assert typeset_names(["k1", "k2"], "latex", names) == {
        "k1": r"\lambda",
        "k2": r"\Omega_{\mathrm{max}}",
    }


def test_typeset_names_reject_ids_which_are_no_sid() -> None:
    """An id which is no SId is never typeset."""
    with pytest.raises(ValueError, match="SId"):
        typeset_names(["a b"], "latex")


@pytest.mark.parametrize("language", ["python", "julia", "r"])
def test_code_names_reject_ids_which_are_no_sid(language: str) -> None:
    """An id which is no SId is never written as code."""
    with pytest.raises(ValueError, match="SId"):
        code_names(["x", "a\nimport os"], language)
