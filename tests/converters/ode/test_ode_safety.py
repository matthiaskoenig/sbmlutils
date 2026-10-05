"""Test the safety of the ODE export: no text and no id of a model becomes code.

libsbml reads a document whose names hold line breaks and whose ids are no SIds and
only reports an error, so a model can hold any text where code or markup is written.
Every format is checked with the same models:

- free text (the names of every element and of the model, the notes, the units and
  the name of the file) with line breaks, control characters and the syntax of
  every language (the end of a docstring, an interpolation, a block comment, the
  end of a string, markup) stays text: no line of a format begins with it, no
  control character but the line break is written, the code parses without a name
  of it (python with `ast`, julia with `Meta.parseall`, R with `parse`) and returns
  it unchanged, and a document compiles (typst, LaTeX) or parses (markdown) with the
  text as text;
- an id which is no SId raises a `ValueError`, in a code format every id, in a
  document every id, which it writes as code or typesets, the model id with line
  breaks included;
- an identifier in math which is no SId raises a `ValueError` in every format;
- a species without a compartment is no invalid id `''`;
- a local parameter keeps its value against a global parameter of its id and a
  global parameter of the id it is renamed to.

The julia and the R code runs in one process of julia and of R each, see `run_jobs`;
those tests skip without the toolchain, see `SBMLUTILS_JULIA` and
`SBMLUTILS_RSCRIPT`.
"""

import ast
import json
import os
import re
import unicodedata
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import libsbml
import pytest
from markdown_it import MarkdownIt
from ode_helpers import (
    JULIA_NAMES_JOB,
    JULIA_POINT_VALUES_JOB,
    LANGUAGES,
    R_NAMES_JOB,
    R_POINT_VALUES_JOB,
    Job,
    JobOutput,
    assert_python_as_roadrunner,
    assert_values_as_roadrunner,
    compile_latex,
    compile_typst,
    edit_sbml,
    import_module,
    markdown_tables,
    model_sbml,
    python_module,
    require_language,
    require_tectonic,
    run_jobs,
    sbml_with_rate,
)

from sbmlutils.converters.ode import OdeSystem
from sbmlutils.converters.ode.text import single_line

CODE_FORMATS = ["python", "julia", "r"]
"""The formats of code."""

DOCUMENT_FORMATS = ["typst", "latex", "markdown"]
"""The formats of documents."""

ALL_FORMATS = CODE_FORMATS + DOCUMENT_FORMATS
"""Every format."""

OTHER_OPTIONS: dict[str, dict[str, object]] = {
    **{fmt: {"simulator": False} for fmt in CODE_FORMATS},
    **{fmt: {"standalone": False} for fmt in DOCUMENT_FORMATS},
}
"""The options of each format which differ from its default, the other shape of its
output: the right hand side only, a fragment."""

INJECTED = (
    # every line break and control character
    "A\nINJECTED_LF = 1\rINJECTED_CR = 1\r\nINJECTED_CRLF = 1"
    "\u2028INJECTED_LS = 1\u2029INJECTED_PS = 1\x85INJECTED_NEL = 1"
    "\x9bINJECTED_CSI = 1\tINJECTED_TAB = 1"
    # python and julia: the end of a docstring, an interpolation, a block comment
    ' """ INJECTED_DOC = 1 $(INJECTED_INTERPOLATION = 1) $x #= INJECTED_BLOCK = 1'
    # R: the end of a string, an escaped quote, unicode and its escape
    ' "); INJECTED_QUOTE <- 1; c(" \\" ä \\u{41}'
    # the markup of the documents
    " `INJECTED_CODE` #strong[INJECTED_STRONG] $x$ _c_ *d* | <script>"
    " \\input{/etc/hostname} % &amp; end\\"
)
"""A text which leaves a comment, a string or the text of a document, if a line
break or a character of the syntax of a format is written as it is."""

FILE_NAME = (
    'm\nINJECTED_FILE = 1 """ $(INJECTED_FILE) #= "); `x` <script> \\input{x} %.xml'
    if os.name == "posix"
    else "injected.xml"
)
"""The name of the file of the model, which windows allows no line break in."""


def xml_text(text: str) -> str:
    """Text as the value of an XML attribute or the content of an element.

    A line break and a control character are written as a character reference,
    which XML keeps, a literal one in an attribute is read as a space.

    Args:
        text: the text

    Returns:
        the escaped text
    """
    escaped = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}
    return "".join(
        escaped.get(char)
        or (
            f"&#x{ord(char):x};"
            if unicodedata.category(char) in {"Cc", "Zl", "Zp"}
            else char
        )
        for char in text
    )


MODEL = """
    function f(x)
        2 * x
    end
    compartment c = 2
    species A in c = 3; species B in c = 0
    k = 0.5
    y := k * 2
    z = 1; z' = -k
    q = 3 * k
    R1: A -> B; k * f(A)
    E1: at time > k: z = 2 * k
"""
"""A model with every element which has an id, completed by `_complete`: function
definition, compartment, species, parameter, assignment rule, rate rule, initial
assignment, reaction, event and, by `_complete`, a species reference with an id, a
local parameter and a unit definition."""


def _complete(model: libsbml.Model) -> None:
    """Complete `MODEL`: model id `m`, species reference id, local parameter, unit."""
    model.setId("m")
    reaction: libsbml.Reaction = model.getReaction("R1")
    reactant: libsbml.SpeciesReference = reaction.getReactant(0)
    reactant.setId("sr")
    law: libsbml.KineticLaw = reaction.getKineticLaw()
    local: libsbml.LocalParameter = law.createLocalParameter()
    local.setId("kl")
    local.setValue(2.0)
    law.setMath(libsbml.parseL3Formula("k * f(A) * kl"))
    unit_definition: libsbml.UnitDefinition = model.createUnitDefinition()
    unit_definition.setId("u")
    for kind, exponent, multiplier in [
        (libsbml.UNIT_KIND_MOLE, 2.0, 2.0),
        (libsbml.UNIT_KIND_METRE, 1.0, 1.0),
        (libsbml.UNIT_KIND_SECOND, -1.0, 1.0),
    ]:
        unit: libsbml.Unit = unit_definition.createUnit()
        unit.setKind(kind)
        unit.setExponent(exponent)
        unit.setMultiplier(multiplier)
        unit.setScale(0)
    parameter: libsbml.Parameter = model.getParameter("k")
    parameter.setUnits("u")


def base_sbml() -> str:
    """The SBML of `MODEL`, completed."""
    return edit_sbml(model_sbml(MODEL), _complete)


def _named(model: libsbml.Model) -> None:
    """Name every element and the model `NAME`, the notes of the model `NOTES`."""
    elements: libsbml.SBaseList = model.getListOfAllElements()
    for k in range(elements.getSize()):
        element: libsbml.SBase = elements.get(k)
        if not isinstance(element, libsbml.ListOf):
            element.setName("NAME")
    model.setName("NAME")
    model.setNotes('<body xmlns="http://www.w3.org/1999/xhtml"><p>NOTES</p></body>')


def injected_sbml() -> str:
    """The SBML of `MODEL` with `INJECTED` as every name and as the notes."""
    sbml = edit_sbml(base_sbml(), _named)
    assert sbml.count('name="NAME"') > 10
    sbml = sbml.replace('name="NAME"', f'name="{xml_text(INJECTED)}"')
    return sbml.replace("<p>NOTES</p>", f"<p>{xml_text(INJECTED)}</p>")


@pytest.fixture(scope="module")
def injected(tmp_path_factory: pytest.TempPathFactory) -> OdeSystem:
    """The system of `injected_sbml`, read from the file `FILE_NAME`."""
    path = tmp_path_factory.mktemp("injected") / FILE_NAME
    path.write_text(injected_sbml(), encoding="utf-8")
    return OdeSystem.from_sbml(path)


def test_injected_model() -> None:
    """The text is read as it is: every name, the notes and the unit."""
    system = OdeSystem.from_sbml(injected_sbml())
    assert system.info.name == INJECTED
    assert system.symbol("A").name == INJECTED
    assert system.events[0].symbol.name == INJECTED
    notes = system.info.notes
    assert notes is not None
    assert "INJECTED_CSI = 1" in notes
    assert "#strong[INJECTED_STRONG]" in notes
    assert system.symbol("k").unit == "(2 mol)^2*m/s"


# --- free text ------------------------------------------------------------------------


def _outputs(system: OdeSystem, fmt: str) -> Iterator[str]:
    """The outputs of a format in its default options and in its other ones."""
    yield system.render(fmt)
    yield system.render(fmt, **OTHER_OPTIONS[fmt])


@pytest.mark.parametrize("fmt", ALL_FORMATS)
def test_text_stays_on_its_line(fmt: str, injected: OdeSystem) -> None:
    """No line begins with injected text, no control character is written."""
    for output in _outputs(injected, fmt):
        assert "INJECTED_LF = 1" in output or "INJECTED\\_LF = 1" in output
        written = {
            char
            for char in output
            if char != "\n" and unicodedata.category(char) in {"Cc", "Zl", "Zp"}
        }
        assert not written
        for line in output.splitlines():
            assert not line.lstrip().startswith("INJECTED"), line


def _identifiers(tree: ast.AST) -> set[str]:
    """Every identifier of python code: names, functions, arguments, attributes."""
    found = set()
    for node in ast.walk(tree):
        for field in ("id", "name", "arg", "attr"):
            value = getattr(node, field, None)
            if isinstance(value, str):
                found.add(value)
    return found


@pytest.mark.parametrize("simulator", [True, False])
def test_python_text_is_no_code(
    simulator: bool, injected: OdeSystem, tmp_path: Path
) -> None:
    """The python code parses without injected names and holds the text unchanged."""
    code = injected.render("python", simulator=simulator)
    assert not {n for n in _identifiers(ast.parse(code)) if "INJECTED" in n}
    path = tmp_path / "injected.py"
    path.write_text(code, encoding="utf-8")
    module = import_module(path)
    assert not [n for n in vars(module) if "INJECTED" in n]
    text = single_line(INJECTED)
    assert module.NAMES["A"] == text
    assert module.UNITS["k"] == "(2 mol)^2*m/s"
    assert module.__doc__ is not None
    assert text in module.__doc__
    assert single_line(FILE_NAME) in module.__doc__


# the body of a julia job which checks the code: its names, the text of a name and the
# docstring of the module, a string unless it interpolates
JULIA_TEXT_JOB = (
    JULIA_NAMES_JOB
    + """
    emit(io, "name", [m.NAMES["A"]])
    emit(io, "unit", [m.UNITS["k"]])
    call = CODE.args[2]
    emit(io, "doc", [call.args[3] isa String ? call.args[3] : "interpolated"])
"""
)

# the body of an R job which checks the code: its names and the text of a name
R_TEXT_JOB = (
    R_NAMES_JOB
    + """
  emit(io, "name", m$NAMES[["A"]])
  emit(io, "unit", m$UNITS[["k"]])
"""
)

COLLISION = """
    compartment c = 1
    species A in c = 3; species B in c = 2
    k = 0.5; R1_k = 7
    R1: A -> ; k * A * R1_k
    R2: B -> ; k * B
"""
"""A model whose reaction R1 gets a local parameter `k`, which hides the global `k`
and is renamed to an id other than the global `R1_k`, see `collision_sbml`."""


def collision_sbml() -> str:
    """The SBML of `COLLISION` with the local parameter `k = 2` of R1."""

    def local(model: libsbml.Model) -> None:
        law: libsbml.KineticLaw = model.getReaction("R1").getKineticLaw()
        parameter: libsbml.LocalParameter = law.createLocalParameter()
        parameter.setId("k")
        parameter.setValue(2.0)

    return edit_sbml(model_sbml(COLLISION), local)


def without_compartment_sbml() -> str:
    """A species in amount without a compartment, which L3 requires."""
    return (
        sbml_with_rate("k*A")
        .replace(' compartment="c"', "", 1)
        .replace('hasOnlySubstanceUnits="false"', 'hasOnlySubstanceUnits="true"')
        .replace("initialConcentration", "initialAmount")
    )


@dataclass(frozen=True)
class _JobSpec:
    """A job of the code of a language, see `jobs`.

    Attributes:
        sbml: the SBML of the model, `None` for the system of `injected`, which
            is read from a file
        options: the options of the rendering
        run: the body of the job of julia and of R
    """

    sbml: Callable[[], str] | None
    options: dict[str, object]
    run: dict[str, str]


JOBS: dict[str, _JobSpec] = {
    "injected_simulator": _JobSpec(
        None,
        {"simulator": True},
        {"julia": JULIA_TEXT_JOB, "r": R_TEXT_JOB},
    ),
    "injected_rhs": _JobSpec(
        None,
        {"simulator": False},
        {"julia": JULIA_TEXT_JOB, "r": R_TEXT_JOB},
    ),
    "collision": _JobSpec(
        collision_sbml,
        {"simulator": False},
        {"julia": JULIA_POINT_VALUES_JOB, "r": R_POINT_VALUES_JOB},
    ),
    "without_compartment": _JobSpec(
        without_compartment_sbml,
        {"simulator": False},
        {"julia": JULIA_POINT_VALUES_JOB, "r": R_POINT_VALUES_JOB},
    ),
}
"""The jobs of julia and R by their name."""


@pytest.fixture(scope="module")
def jobs(
    tmp_path_factory: pytest.TempPathFactory, injected: OdeSystem
) -> Callable[[str, str], JobOutput]:
    """The output of a job of `JOBS` in a language.

    The jobs of a language run in one process, on the first request of one of them.
    """
    outputs: dict[str, dict[str, JobOutput]] = {}

    def output(language: str, name: str) -> JobOutput:
        require_language(language)
        if language not in outputs:
            directory = tmp_path_factory.mktemp(f"safety_{language}")
            suffix = LANGUAGES[language].suffix
            language_jobs = {}
            for job_name, spec in JOBS.items():
                path = (directory / f"{job_name}{suffix}").absolute()
                system = (
                    injected if spec.sbml is None else OdeSystem.from_sbml(spec.sbml())
                )
                code = system.render(language, **spec.options)
                run = spec.run[language].replace("{path}", str(path))
                language_jobs[job_name] = Job(code, run)
            outputs[language] = run_jobs(language, language_jobs, directory)
        return outputs[language][name]

    return output


@pytest.mark.parametrize("name", ["injected_simulator", "injected_rhs"])
def test_julia_text_is_no_code(
    name: str, jobs: Callable[[str, str], JobOutput]
) -> None:
    """The julia code parses without injected names and holds the text unchanged."""
    output = jobs("julia", name)
    assert not [n for n in output.strings("names") if "INJECTED" in n]
    text = single_line(INJECTED)
    assert output.strings("name") == [text]
    assert output.strings("unit") == ["(2 mol)^2*m/s"]
    doc = output.strings("doc")[0]
    assert text in doc
    assert single_line(FILE_NAME) in doc


@pytest.mark.parametrize("name", ["injected_simulator", "injected_rhs"])
def test_r_text_is_no_code(name: str, jobs: Callable[[str, str], JobOutput]) -> None:
    """The R code parses without injected names and holds the text unchanged."""
    output = jobs("r", name)
    assert not [n for n in output.strings("names") if "INJECTED" in n]
    assert output.strings("name") == [single_line(INJECTED)]
    assert output.strings("unit") == ["(2 mol)^2*m/s"]


def test_r_strings_are_ascii(injected: OdeSystem) -> None:
    """The strings of the R code are ASCII, whatever the locale R reads the file in.

    A text which is no ASCII, `ä`, is written with its escape in a string, and as it
    is only in a comment.
    """
    for code in _outputs(injected, "r"):
        for line in code.splitlines():
            if not line.isascii():
                assert "#" in line, line
                assert line[: line.index("#")].isascii(), line


@pytest.mark.parametrize("fmt", DOCUMENT_FORMATS)
def test_document_text_is_no_markup(fmt: str, injected: OdeSystem) -> None:
    """The text of a document is escaped: it writes no markup of its format."""
    for output in _outputs(injected, fmt):
        if fmt == "typst":
            assert "#strong[INJECTED_STRONG]" not in output
            assert r"\#strong\[INJECTED\_STRONG\]" in output
        elif fmt == "latex":
            assert "\\input" not in output
            assert r"\textbackslash{}input\{/etc/hostname\} \%" in output
        else:
            assert "<script>" not in output
            assert "&lt;script&gt;" in output


@pytest.mark.parametrize("fmt", ["standalone", "fragment"])
def test_typst_of_text_compiles(fmt: str, injected: OdeSystem, tmp_path: Path) -> None:
    """The typst document with the injected text compiles."""
    if fmt == "standalone":
        compile_typst(injected.render("typst"), tmp_path)
    else:
        fragment = injected.render("typst", standalone=False)
        compile_typst(f"= Supplement\n\n{fragment}", tmp_path)


TYPST_ELEMENTS = [
    "strong",
    "emph",
    "raw",
    "math.equation",
    "link",
    "list",
    "enum",
    "terms",
    "ref",
    "footnote",
]
"""The elements of typst which markup in a text would add to a document."""


def _typst_elements(source: str, tmp_path: Path) -> dict[str, object]:
    """The elements of a compiled typst document which markup would add.

    Each of `TYPST_ELEMENTS` as the set of its distinct elements, a header of a
    table is repeated on every page it spans; the headings by their number, the
    title holds the name of the model.
    """
    compile_typst(source, tmp_path)
    import typst

    path = str(tmp_path / "document.typ")
    elements: dict[str, object] = {
        selector: {
            json.dumps(element, sort_keys=True)
            for element in json.loads(typst.query(path, selector))
        }
        for selector in TYPST_ELEMENTS
    }
    elements["heading"] = len(json.loads(typst.query(path, "heading")))
    return elements


@pytest.mark.parametrize("standalone", [True, False])
def test_typst_of_text_is_no_markup(
    standalone: bool, injected: OdeSystem, tmp_path: Path
) -> None:
    """The compiled typst document holds the injected text as text, not as markup.

    The compiled document has the elements of markup (strong and emphasized text,
    code, equations, links, lists, references, footnotes and the number of
    headings) of the document of the same model with plain names and notes.
    """
    plain_path = tmp_path / "plain.xml"
    plain_path.write_text(edit_sbml(base_sbml(), _named), encoding="utf-8")
    plain = OdeSystem.from_sbml(plain_path)
    elements = []
    for k, system in enumerate([plain, injected]):
        document = system.render("typst", standalone=standalone)
        if not standalone:
            document = f"= Supplement\n\n{document}"
        directory = tmp_path / str(k)
        directory.mkdir()
        elements.append(_typst_elements(document, directory))
    assert elements[1] == elements[0]
    assert elements[0]["strong"]
    assert elements[0]["math.equation"]


def test_latex_of_text_compiles(injected: OdeSystem, tmp_path: Path) -> None:
    """The LaTeX document with the injected text compiles without a warning."""
    require_tectonic()
    compile_latex(injected.render("latex"), tmp_path, strict=True)


def test_markdown_of_text_is_text(injected: OdeSystem) -> None:
    """The markdown with the injected text writes it as text, in its table cells.

    The markdown has no HTML but the superscripts of the units, no emphasis and no
    link, its only strong text is the heading of an event, and the text of a name
    in a cell is the name.
    """
    markdown = injected.render("markdown")
    tokens = MarkdownIt("gfm-like", {"linkify": False}).parse(markdown)
    inline = [child for t in tokens for child in t.children or []]
    types = {t.type for t in [*tokens, *inline]}
    assert not types & {"html_block", "em_open", "link_open"}
    html = {t.content for t in inline if t.type == "html_inline"}
    assert html == {"<sup>", "</sup>"}
    assert sum(t.type == "strong_open" for t in inline) == len(injected.events)
    assert "INJECTED_CODE" not in [t.content for t in inline if t.type == "code_inline"]
    for table in markdown_tables(markdown):
        assert len({len(row) for row in table}) == 1
    cells = []
    in_cell = False
    for token in tokens:
        if token.type in ("th_open", "td_open"):
            in_cell = True
        elif token.type in ("th_close", "td_close"):
            in_cell = False
        elif token.type == "inline" and in_cell:
            children = token.children or []
            text = {"text", "text_special"}
            cells.append("".join(c.content for c in children if c.type in text))
    # the compartment, the species, the parameters and the reaction
    assert cells.count(single_line(INJECTED)) >= 5


MARKUP = "a $x$ #b _c_ | d \\ <script>"
"""A name which is markup in every format."""


@pytest.mark.parametrize("fmt", DOCUMENT_FORMATS)
def test_markup_in_names_is_text(fmt: str, tmp_path: Path) -> None:
    """A name is written as text in every format, never as its markup."""
    system = OdeSystem.from_sbml(sbml_with_rate("k * A", name=xml_text(MARKUP)))
    document = system.render(fmt)
    assert "<script>" not in document
    if fmt == "typst":
        assert r"a \$x\$ \#b \_c\_ | d \\ \<script\>" in document
        compile_typst(document, tmp_path)
        fragment = system.render(fmt, standalone=False)
        compile_typst(f"= Supplement\n\n{fragment}", tmp_path)
    elif fmt == "latex":
        assert (
            r"a \$x\$ \#b \_c\_ \textbar{} d \textbackslash{} "
            r"\textless{}script\textgreater{}"
        ) in document
        require_tectonic()
        compile_latex(document, tmp_path, strict=True)
    else:
        escaped = r"a \$x\$ #b \_c\_ \| d \\ &lt;script&gt;"
        assert escaped in document
        # the pipe does not split the cell of the name, whose content the table
        # unescapes
        names = [row[2] for table in markdown_tables(document)[1:] for row in table[1:]]
        assert names == [escaped.replace("\\|", "|")] * 3


# --- ids ------------------------------------------------------------------------------

INVALID_ID = 'm\n\\input{/etc/hostname}\nINJECTED = 1 #"$<b>`'
"""An id which is no SId: it breaks the line, ends a string and writes markup."""

IDS = ["m", "f", "c", "A", "k", "y", "z", "q", "R1", "E1", "sr", "kl"]
"""The id of every element of `base_sbml`, the model `m` first."""


@pytest.mark.parametrize("fmt", ALL_FORMATS)
@pytest.mark.parametrize("sid", IDS)
def test_ids_which_are_no_sid_are_rejected(sid: str, fmt: str) -> None:
    """Every id, the model id with line breaks included, is checked to be an SId."""
    # the id where it is declared and wherever it is used
    pattern = re.compile(rf'(?<=["\s>]){re.escape(sid)}(?=["\s<])')
    sbml, count = pattern.subn(lambda _: xml_text(INVALID_ID), base_sbml())
    assert count
    system = OdeSystem.from_sbml(sbml)
    with pytest.raises(ValueError, match="SId"):
        system.render(fmt)


@pytest.mark.parametrize("fmt", ALL_FORMATS)
def test_function_argument_which_is_no_sid_is_rejected(fmt: str) -> None:
    """An argument of a function definition is checked to be an SId."""
    sbml = base_sbml()
    # the argument `x` of `f` and its use in the body of `f`
    assert sbml.count("<ci> x </ci>") == 2
    sbml = sbml.replace("<ci> x </ci>", f"<ci> {xml_text(INVALID_ID)} </ci>")
    system = OdeSystem.from_sbml(sbml)
    with pytest.raises(ValueError, match="SId"):
        system.render(fmt)


INVALID_NAME = "k\nINJECTED = 1 + __import__('os') \\input{/etc/hostname}"
"""An identifier in math which is no SId, a line of code and markup."""


MathElement = (
    libsbml.KineticLaw
    | libsbml.Rule
    | libsbml.InitialAssignment
    | libsbml.FunctionDefinition
    | libsbml.Trigger
    | libsbml.EventAssignment
)
"""An element of SBML with math."""


def _math_element(where: str, model: libsbml.Model) -> MathElement:
    """The element of `base_sbml` with math of the place `where`."""
    elements: dict[str, Callable[[], MathElement]] = {
        "rate law": lambda: model.getReaction("R1").getKineticLaw(),
        "assignment rule": lambda: model.getRuleByVariable("y"),
        "rate rule": lambda: model.getRuleByVariable("z"),
        "initial assignment": lambda: model.getInitialAssignmentBySymbol("q"),
        "function definition": lambda: model.getFunctionDefinition("f"),
        "trigger": lambda: model.getEvent("E1").getTrigger(),
        "event assignment": lambda: model.getEvent("E1").getEventAssignment(0),
    }
    return elements[where]()


def _rename_first_name(ast_node: libsbml.ASTNode, new: str) -> bool:
    """Rename the first name of math which is no bound variable, `True` if found."""
    if ast_node.getType() == libsbml.AST_NAME and not ast_node.isBvar():
        ast_node.setName(new)
        return True
    return any(
        _rename_first_name(ast_node.getChild(k), new)
        for k in range(ast_node.getNumChildren())
    )


@pytest.mark.parametrize("fmt", ALL_FORMATS)
@pytest.mark.parametrize(
    "where",
    [
        "rate law",
        "assignment rule",
        "rate rule",
        "initial assignment",
        "function definition",
        "trigger",
        "event assignment",
    ],
)
def test_identifiers_in_math_which_are_no_sid_are_rejected(
    where: str, fmt: str
) -> None:
    """An identifier in math which is no SId is never written."""

    def invalid(model: libsbml.Model) -> None:
        element = _math_element(where, model)
        math: libsbml.ASTNode = element.getMath().deepCopy()
        assert _rename_first_name(math, INVALID_NAME)
        assert element.setMath(math) == libsbml.LIBSBML_OPERATION_SUCCESS

    system = OdeSystem.from_sbml(edit_sbml(base_sbml(), invalid))
    with pytest.raises(ValueError, match="SId"):
        system.render(fmt)


# --- a species without a compartment --------------------------------------------------


@pytest.mark.parametrize("fmt", ALL_FORMATS)
def test_species_without_compartment(fmt: str) -> None:
    """A species in amount without a compartment is no invalid id `''`.

    A document leaves the compartment of the species empty.
    """
    system = OdeSystem.from_sbml(without_compartment_sbml())
    for output in _outputs(system, fmt):
        assert "A" in output
    document = system.render(fmt)
    if fmt == "markdown":
        (species,) = [t for t in markdown_tables(document) if "Properties" in t[0]]
        assert species[0][3] == "Compartment"
        assert species[1][1:5] == ["`A`", "species A", "", "$3$"]
    elif fmt == "typst":
        assert "[`A`], [species A], [], [$3$]," in document
    elif fmt == "latex":
        assert r"\texttt{A} & species A &  & $3$" in document


def test_typst_without_compartment_compiles(tmp_path: Path) -> None:
    """The typst document of a species without a compartment compiles."""
    system = OdeSystem.from_sbml(without_compartment_sbml())
    compile_typst(system.render("typst"), tmp_path)


def test_latex_without_compartment_compiles(tmp_path: Path) -> None:
    """The LaTeX document of a species without a compartment compiles."""
    require_tectonic()
    system = OdeSystem.from_sbml(without_compartment_sbml())
    compile_latex(system.render("latex"), tmp_path, strict=True)


def test_python_species_without_compartment(tmp_path: Path) -> None:
    """The python code of a species without a compartment computes its rate.

    roadrunner does not read the model, `dA/dt = -k A = -0.5 * 3`.
    """
    system = OdeSystem.from_sbml(without_compartment_sbml())
    module = python_module(system, tmp_path / "model.py", simulator=False)
    x0, p = module.initial_values()
    assert module.f_dxdt(0.0, x0, p).tolist() == [-1.5]


@pytest.mark.parametrize("language", ["julia", "r"])
def test_species_without_compartment_runs(
    language: str, jobs: Callable[[str, str], JobOutput]
) -> None:
    """The julia and R code of a species without a compartment computes its rate."""
    values = jobs(language, "without_compartment").point_values()
    assert values.x0.tolist() == [3.0]
    _, _, dxdt, _ = values.points[0]
    assert dxdt.tolist() == [-1.5]


def test_species_in_concentration_without_compartment() -> None:
    """A species in concentration needs its compartment, which is named as missing."""
    sbml = sbml_with_rate("k*A").replace(' compartment="c"', "", 1)
    with pytest.raises(ValueError, match=r"'A'.*compartment") as error:
        OdeSystem.from_sbml(sbml)
    assert "SId" not in str(error.value)


# --- local parameters -----------------------------------------------------------------


def test_local_parameter_is_renamed_apart() -> None:
    """The local `k` of R1 is renamed apart from the global `k` and `R1_k`."""
    system = OdeSystem.from_sbml(collision_sbml())
    (renamed,) = system.reactions[0].local_parameters
    assert renamed not in {"k", "R1_k"}
    assert system.quantity(renamed).value == 2.0
    assert system.quantity("k").value == 0.5
    assert system.quantity("R1_k").value == 7.0


def test_python_local_parameter_as_roadrunner(tmp_path: Path) -> None:
    """The python code of the colliding local parameter computes as roadrunner."""
    assert_python_as_roadrunner(collision_sbml(), tmp_path)


@pytest.mark.parametrize("language", ["julia", "r"])
def test_local_parameter_as_roadrunner(
    language: str, jobs: Callable[[str, str], JobOutput]
) -> None:
    """The julia and R code of the colliding local parameter computes as roadrunner."""
    assert_values_as_roadrunner(
        collision_sbml(), jobs(language, "collision").point_values()
    )


@pytest.mark.parametrize("fmt", DOCUMENT_FORMATS)
def test_document_local_parameter(fmt: str) -> None:
    """A document lists the renamed local parameter apart from both globals."""
    system = OdeSystem.from_sbml(collision_sbml())
    (renamed,) = system.reactions[0].local_parameters
    document = system.render(fmt)
    escape = {"typst": "_", "latex": r"\_", "markdown": "_"}[fmt]
    for sid in ("R1_k", renamed):
        assert sid.replace("_", escape) in document
