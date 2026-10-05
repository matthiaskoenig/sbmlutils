"""Test the presentation formats of the ODE export: typst, LaTeX and markdown.

The documents of the demo model, the repressilator and a model with events, function
definitions, an amount state and initial assignments are compared with the golden
files in `golden/`, which are regenerated with `SBMLUTILS_UPDATE_GOLDEN=1`, and are
compiled: typst with the `typst` package, LaTeX with tectonic (skipped without it on
the path, failed with `SBMLUTILS_REQUIRE_TOOLCHAINS`), markdown parsed with
markdown-it-py.
"""

import os
import re
from pathlib import Path

import libsbml
import pytest
from markdown_it import MarkdownIt
from ode_helpers import (
    compile_latex,
    compile_typst,
    edit_sbml,
    model_sbml,
    require_tectonic,
    sbml_with_rate,
)
from test_ode_symbols import SYMBOLS

import sbmlutils
from sbmlutils.converters.ode import FORMATS, OdeSystem
from sbmlutils.converters.ode.documents import DocumentContext
from sbmlutils.resources import DEMO_SBML, REPRESSILATOR_SBML

GOLDEN = Path(__file__).parent / "golden"
"""The directory of the golden documents."""

UPDATE_GOLDEN = "SBMLUTILS_UPDATE_GOLDEN"
"""The environment variable which writes the golden documents instead of comparing."""

SUFFIXES = {"typst": ".typ", "latex": ".tex", "markdown": ".md"}
"""The suffix of each document format."""

EVENTS = """
    function mm(S, km)
      S / (km + S)
    end

    model events_model
      compartment c = 1, V = 2
      V' = 0.1
      species S in c = 10, P in c = 0, A in V = 5, B in V = 1
      B' = -0.1 * B
      J0: S -> P; vmax * mm(S, km)
      J1: S + A -> 2 P; k1 * S * A
      vmax = 2; km = 0.5; k1 = 0.1
      k2 := 2 * k1
      S0 = 10
      S = S0
      total = 0
      E1: at time > 5, priority = 1: S = 10, V = 2 * V
      E2: at 1 after S < 2: total = total + 1, A = 1
      S is "substrate"
      E1 is "reset"
    end
"""
"""A model with events, a function definition, a rate rule of a compartment, an
amount state, an initial assignment and an assignment rule, the source of
`golden/events.xml`."""

MODELS: dict[str, Path | str] = {
    "demo": DEMO_SBML,
    "repressilator": REPRESSILATOR_SBML,
    # the SBML which antimony writes, fixed, because the order of the event
    # assignments of antimony depends on its version
    "events": GOLDEN / "events.xml",
}
"""The models of the golden documents."""


def test_events_model() -> None:
    """The events model is the SBML of its antimony, but for the order."""

    def lines(system: OdeSystem) -> list[str]:
        """The lines of the markdown, without the line breaks of an alignment."""
        markdown = system.render("markdown")
        return sorted(line.removesuffix(" \\\\") for line in markdown.splitlines())

    system = OdeSystem.from_sbml(model_sbml(EVENTS))
    golden = OdeSystem.from_sbml((GOLDEN / "events.xml").read_text())
    assert lines(system) == lines(golden)


@pytest.fixture
def version(monkeypatch: pytest.MonkeyPatch) -> None:
    """The version of sbmlutils is `VERSION`, so that the goldens outlive a release."""
    monkeypatch.setattr(sbmlutils, "__version__", "VERSION")


def render(name: str, fmt: str, **options: object) -> str:
    """The document of a golden model."""
    return OdeSystem.from_sbml(MODELS[name]).render(fmt, **options)


# --- golden documents -----------------------------------------------------------------


@pytest.mark.usefixtures("version")
@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
@pytest.mark.parametrize("name", sorted(MODELS))
def test_golden(name: str, fmt: str) -> None:
    """The standalone document is the golden document."""
    document = render(name, fmt)
    path = GOLDEN / f"{name}{SUFFIXES[fmt]}"
    if os.environ.get(UPDATE_GOLDEN):
        path.write_text(document, encoding="utf-8")
    assert document == path.read_text(encoding="utf-8")


@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
def test_formats(fmt: str) -> None:
    """The document formats take the options standalone and symbols."""
    assert FORMATS[fmt].kind == "document"
    assert FORMATS[fmt].options == {"standalone": True, "symbols": "id"}


@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
def test_document_is_whole_lines(fmt: str) -> None:
    """A document ends with a line break and has no trailing white space."""
    for name in MODELS:
        document = render(name, fmt)
        assert document.endswith("\n")
        assert not document.endswith("\n\n")
        assert not re.search(r"[ \t]$", document, re.MULTILINE), name
        assert "\n\n\n" not in document, name


def test_fragments() -> None:
    """A fragment is the content of a document, to include in another one."""
    typst = render("demo", "typst", standalone=False)
    assert "#set page" not in typst
    assert "#set document" not in typst
    # the rules of the fragment apply within its content block only
    assert typst.startswith("// The content of a typst document")
    assert "\n#[\n// the equations of a section" in typst
    assert typst.endswith("\n]\n")
    assert "\n= Koenig\\_demo\\_v15\n" in typst
    assert "\n== Units\n" in typst

    latex = render("demo", "latex", standalone=False)
    assert r"\documentclass" not in latex
    assert r"\begin{document}" not in latex
    assert r"\end{document}" not in latex
    assert latex.startswith("% The body of a LaTeX document")
    assert "amsmath, amssymb, booktabs\n% and xltabular" in latex
    # the title may break after an underscore, the bookmark is plain
    assert (
        "\\section{\\texorpdfstring{Koenig\\_\\allowbreak{}demo\\_\\allowbreak{}v15}"
        "{Koenig\\_demo\\_v15}}"
    ) in latex
    assert "\\subsection{Units}" in latex

    markdown = render("demo", "markdown", standalone=False)
    assert markdown.startswith("## Koenig\\_demo\\_v15\n")
    assert "\n### Units\n" in markdown

    standalone = render("demo", "markdown")
    assert standalone.startswith("# Koenig\\_demo\\_v15\n")
    assert "\n## Units\n" in standalone


def test_write_by_suffix(tmp_path: Path) -> None:
    """The format of a document is the suffix of its file."""
    system = OdeSystem.from_sbml(MODELS["events"])
    for fmt, suffix in SUFFIXES.items():
        path = system.write(tmp_path / f"model{suffix}", standalone=False)
        assert path.read_text(encoding="utf-8") == system.render(fmt, standalone=False)


def test_options() -> None:
    """The symbols are made of the ids or the names, the standalone flag is a bool."""
    system = OdeSystem.from_sbml(MODELS["events"])
    with pytest.raises(ValueError, match="'id' or 'name'"):
        system.render("typst", symbols="sid")
    with pytest.raises(ValueError, match="standalone"):
        system.render("latex", standalone="yes")
    with pytest.raises(ValueError, match="simulator"):
        system.render("markdown", simulator=True)


# --- typst ----------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(MODELS))
def test_typst_compiles(name: str, tmp_path: Path) -> None:
    """The typst document compiles without a warning."""
    assert compile_typst(render(name, "typst"), tmp_path).startswith(b"%PDF")


@pytest.mark.parametrize("name", sorted(MODELS))
def test_typst_fragment_compiles(name: str, tmp_path: Path) -> None:
    """The typst fragment compiles, included into a document."""
    (tmp_path / "fragment.typ").write_text(
        render(name, "typst", standalone=False), encoding="utf-8"
    )
    wrapper = (
        '#set page(paper: "a4", margin: 2cm)\n'
        '#set heading(numbering: "1.")\n\n'
        "= Supplement\n\n"
        '#include "fragment.typ"\n'
    )
    assert compile_typst(wrapper, tmp_path).startswith(b"%PDF")


# --- LaTeX ----------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(MODELS))
def test_latex_compiles(name: str, tmp_path: Path) -> None:
    """The LaTeX document compiles with tectonic."""
    require_tectonic()
    assert compile_latex(render(name, "latex"), tmp_path, strict=True).exists()


TITLED = edit_sbml(
    model_sbml("A = 0; A' = 1"),
    lambda model: model.setName("Model α with a $x$ | y"),
)
"""A model whose name holds a greek letter and markup, a title which is no PDF string."""


@pytest.mark.parametrize("hyperref", [False, True])
@pytest.mark.parametrize("sbml", ["demo", "titled"])
def test_latex_fragment_compiles(sbml: str, hyperref: bool, tmp_path: Path) -> None:
    """The LaTeX fragment compiles with the packages it names, input into a document.

    The title of the demo is its id, with opportunities of line breaks, the title of
    `TITLED` a name with a greek letter and markup: with hyperref the bookmark of
    either is a plain form of the title, without hyperref the title itself.
    """
    require_tectonic()
    source = MODELS["demo"] if sbml == "demo" else TITLED
    (tmp_path / "fragment.tex").write_text(
        OdeSystem.from_sbml(source).render("latex", standalone=False),
        encoding="utf-8",
    )
    packages = "amsmath, amssymb, booktabs, xltabular" + (
        ", hyperref" if hyperref else ""
    )
    wrapper = (
        "\\documentclass{article}\n"
        "\\usepackage{fontspec}\n"
        f"\\usepackage{{{packages}}}\n"
        "\\allowdisplaybreaks\n"
        "\\begin{document}\n"
        "\\input{fragment}\n"
        "\\end{document}\n"
    )
    assert compile_latex(wrapper, tmp_path, strict=True).exists()


def test_latex_title_of_a_name() -> None:
    """A title from a name has a form without math for the bookmarks of a PDF."""
    document = OdeSystem.from_sbml(TITLED).render("latex", standalone=False)
    assert (
        r"\section{\texorpdfstring{Model \ensuremath{\alpha} with a \$x\$ "
        r"\textbar{} y}{Model α with a \$x\$ \textbar{} y}}"
    ) in document
    assert "\\providecommand{\\texorpdfstring}[2]{#1}\n" in document


def test_latex_symbols_compile(tmp_path: Path) -> None:
    """Every LaTeX symbol compiles, in a sum, a power, a fraction and a subscript."""
    require_tectonic()
    body = "\n\n".join(
        rf"\[ {symbol} + {symbol}^{{2}} + \frac{{{symbol}}}{{{symbol}}} "
        rf"+ n_{{{symbol}}} \]"
        for _, symbol, _ in SYMBOLS
    )
    document = (
        "\\documentclass{article}\n\\usepackage{amsmath}\n\\begin{document}\n"
        f"{body}\n\\end{{document}}\n"
    )
    assert compile_latex(document, tmp_path, strict=True).exists()


# --- markdown -------------------------------------------------------------------------


def _tables(markdown: str) -> list[list[list[str]]]:
    """The tables of a markdown document, each a list of rows of the text of cells."""
    tables: list[list[list[str]]] = []
    cell = False
    for token in MarkdownIt("gfm-like", {"linkify": False}).parse(markdown):
        if token.type == "table_open":
            tables.append([])
        elif token.type == "tr_open":
            tables[-1].append([])
        elif token.type in ("th_open", "td_open"):
            tables[-1][-1].append("")
            cell = True
        elif token.type in ("th_close", "td_close"):
            cell = False
        elif token.type == "inline" and cell:
            tables[-1][-1][-1] = token.content
    return tables


@pytest.mark.parametrize("name", sorted(MODELS))
def test_markdown_tables(name: str) -> None:
    """Every table has a header and a row per element, all rows of its width."""
    system = OdeSystem.from_sbml(MODELS[name])
    markdown = system.render("markdown")
    tables = _tables(markdown)
    expected = [
        len(rows)
        for rows in (
            [system.info.units] if any(system.info.units.values()) else [],
            system.compartments,
            system.species,
            (*system.parameters, *system.species_references),
            system.reactions,
        )
        if rows
    ]
    assert [len(table) - 1 for table in tables] == expected
    for table in tables:
        assert len({len(row) for row in table}) == 1


@pytest.mark.parametrize("name", sorted(MODELS))
def test_markdown_math_blocks(name: str) -> None:
    """The display math is in balanced `$$` blocks without a blank line."""
    markdown = render(name, "markdown")
    blocks = re.findall(r"^\$\$\n(.*?)\n\$\$$", markdown, re.MULTILINE | re.DOTALL)
    assert markdown.count("$$") == 2 * len(blocks)
    for block in blocks:
        assert block.startswith("\\begin{aligned}\n")
        assert block.endswith("\n\\end{aligned}")
        assert "\n\n" not in block
        # no line begins with a sign, which markdown would read as a list
        assert not re.search(r"^\s*[-+*]", block, re.MULTILINE)
    # inline math is balanced in every paragraph and cell
    for line in markdown.splitlines():
        if line != "$$":
            assert line.replace("\\$", "").count("$") % 2 == 0, line


# --- content --------------------------------------------------------------------------

MARKUP = "a $x$ #b _c_ | d \\ <script>"
"""A name which is markup in every format."""


@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
def test_markup_in_names_is_text(fmt: str, tmp_path: Path) -> None:
    """A name is written as text in every format, never as its markup."""
    xml_name = MARKUP.replace("<", "&lt;").replace(">", "&gt;")
    system = OdeSystem.from_sbml(sbml_with_rate("k * A", name=xml_name))
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
        names = [row[2] for table in _tables(document)[1:] for row in table[1:]]
        assert names == [escaped.replace("\\|", "|")] * 3


INVALID_ID = "E2` #strong[pwn] | x <script>"
"""An id which is no SId and which would end the code it is written into."""


@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
@pytest.mark.parametrize("element", ["event", "model"])
def test_ids_which_are_no_sid_are_rejected(fmt: str, element: str) -> None:
    """An id is written as code only if it is an SId, libsbml reads any id."""
    sbml = (GOLDEN / "events.xml").read_text()
    old = 'id="E2"' if element == "event" else 'id="events_model"'
    assert old in sbml
    escaped = INVALID_ID.replace("<", "&lt;").replace(">", "&gt;")
    system = OdeSystem.from_sbml(sbml.replace(old, f'id="{escaped}"'))
    with pytest.raises(ValueError, match="SId"):
        system.render(fmt)


@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
def test_unsupported_element_with_a_metaid(fmt: str) -> None:
    """An unsupported element without an id is labelled with its metaid."""

    def algebraic(model: libsbml.Model) -> None:
        rule: libsbml.AlgebraicRule = model.createAlgebraicRule()
        rule.setMetaId("meta-rule.1")
        rule.setMath(libsbml.parseL3Formula("x + y - 3"))

    sbml = edit_sbml(model_sbml("x = 1; y = 2"), algebraic)
    document = OdeSystem.from_sbml(sbml).render(fmt)
    code = {"typst": "`meta-rule.1`", "latex": r"\texttt{meta-rule.1}"}
    assert f"algebraic rule {code.get(fmt, '`meta-rule.1`')}" in document


@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
def test_symbols_name_option(fmt: str) -> None:
    """With `symbols="name"` an element whose name is a symbol is written with it."""
    sbml = model_sbml("""
        compartment cell = 1
        species S_1 in cell = 2; species S_2 in cell = 0
        J1: S_1 -> S_2; k1 * S_1
        k1 = 0.1
        S_1 is "Glc"; S_2 is "Glc_6P"; J1 is "GK"; k1 is "k_GK"; cell is "a cell"
    """)
    system = OdeSystem.from_sbml(sbml)
    by_id = system.render(fmt)
    by_name = system.render(fmt, symbols="name")
    if fmt == "typst":
        assert "$S_(1)$" in by_id
        assert '$upright("Glc")$' in by_name
        assert '$v_("J1")$' in by_id
        assert '$v_("GK")$' in by_name
        assert '$k_("GK")$' in by_name
        # a name which is no symbol is written with the id
        assert '$upright("cell")$' in by_name
    else:
        assert r"$S_{1}$" in by_id
        assert r"$\mathrm{Glc}$" in by_name
        assert r"$\mathrm{Glc}_{\mathrm{6P}}$" in by_name
        assert r"$v_{\mathrm{J1}}$" in by_id
        assert r"$v_{\mathrm{GK}}$" in by_name
        assert r"$\mathrm{cell}$" in by_name


def test_symbols_are_unique() -> None:
    """A rate or an amount whose symbol is taken is written with its id."""
    sbml = model_sbml("""
        species A = 1
        J0: A -> ; k * A
        k = 1; v_J0 = 2
    """)
    document = OdeSystem.from_sbml(sbml).render("latex")
    # the parameter v_J0 is v_{J0}, the rate of J0 the symbol of its id
    assert r"$v_{\mathrm{J0}}$ & \texttt{v\_J0}" in document
    assert r"$J_{0}$ & \texttt{J0}" in document


@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
def test_unsupported_section(fmt: str) -> None:
    """A document lists the constructs which the ODE system does not express."""
    system = OdeSystem.from_sbml(model_sbml("x = 1; y = 2; 0 = x + y - 3"))
    assert system.unsupported
    document = system.render(fmt)
    assert "Unsupported constructs" in document
    assert "does not express" in document
    # antimony names the rule `_alg0`
    code = {"typst": "`_alg0`", "latex": r"\texttt{\_alg0}", "markdown": "`_alg0`"}
    assert f"algebraic rule {code[fmt]}" in document


def test_events_section() -> None:
    """An event shows its trigger, delay, priority, flags and assignments."""
    document = render("events", "latex")
    section = document[document.index(r"\section{Events}") :]
    assert r"\textbf{Event \texttt{E1}} (reset)" in section
    assert r"\item Trigger: $t > 5$" in section
    assert r"\item Priority: $1$" in section
    assert r"\item Delay: $1$" in section
    assert r"\item Trigger: $S < 2$" in section
    assert (
        r"\texttt{initialValue} true, \texttt{persistent} true, "
        r"\texttt{useValuesFromTriggerTime} true"
    ) in section
    # the assignments, with the conversions of the sizes
    assert r"V &\mathrel{:=} 2 \cdot V \\" in section
    assert r"B &\mathrel{:=} \frac{B \cdot V}{V^{\mathrm{new}}}" in section
    # the concentration 1 converted to the amount is the size
    assert r"n_{A} &\mathrel{:=} V \\" in section
    assert r"$n_{A}$ is the amount of $A$" in section
    assert r"$B$ is converted from the size of $V$" in section


def test_events_section_without_delay_and_priority() -> None:
    """The delay and the priority are left out of an event without them."""
    system = OdeSystem.from_sbml(
        model_sbml("""
        A = 0; A' = 1
        E1: at A > 1, t0=false, persistent=false, fromTrigger=false: A = 0
    """)
    )
    document = system.render("markdown")
    section = document[document.index("## Events") :]
    assert "Delay" not in section
    assert "Priority" not in section
    assert (
        "`initialValue` false, `persistent` false, `useValuesFromTriggerTime` false"
    ) in section
    assert r"A &\mathrel{:=} 0" in section


def test_amount_state() -> None:
    """A species in a compartment of variable size is integrated as its amount."""
    document = render("events", "latex")
    assert r"\frac{\mathrm{d} n_{A}}{\mathrm{d} t} &= -v_{\mathrm{J1}}" in document
    assert r"A &= \frac{n_{A}}{V}" in document
    assert r"n_{A} &= A \cdot V" in document
    assert (
        r"The species $A$ in the compartment $V$ of variable size is integrated as "
        r"its amount $n_{A}$, its concentration is $A = n_{A} / V$."
    ) in document


def test_rate_rules_are_marked() -> None:
    """The ODE of a rate rule is marked."""
    document = render("events", "typst")
    assert '(dif V)/(dif t) &= 0.1 quad "(rate rule)"' in document
    assert '(dif B)/(dif t) &= -0.1 dot B quad "(rate rule)"' in document
    assert "with the rates of the reactions and the rate rules:" in document
    rules = OdeSystem.from_sbml(model_sbml("A = 0; A' = 1")).render("typst")
    assert "with the rate rules:" in rules


def test_functions_section() -> None:
    """A function definition is written as `f(x, y) = ...`."""
    document = render("events", "markdown")
    assert (
        r"\mathrm{mm}\mathopen{}\left(S, \mathrm{km}\right) &= "
        r"\frac{S}{\mathrm{km} + S}"
    ) in document


def test_reaction_equations() -> None:
    """A reaction is written with its stoichiometries, arrow and modifiers."""
    sbml = model_sbml("""
        species A = 1, B = 1, C = 0, M = 1
        J0: 2 A + B => C; k * A * M
        J1: C -> ; k * C
        J2: => A; k
        k = 1
    """)
    document = OdeSystem.from_sbml(sbml).render("latex")
    assert r"$2 \, A + B \longrightarrow C$ & $M$" in document
    assert r"$C \rightleftharpoons \varnothing$ &  \\" in document
    assert r"$\varnothing \longrightarrow A$ &  \\" in document


def test_reaction_with_local_parameters() -> None:
    """The local parameters of a reaction are named in its row."""

    def local(model: libsbml.Model) -> None:
        law: libsbml.KineticLaw = model.getReaction("J0").getKineticLaw()
        parameter: libsbml.LocalParameter = law.createLocalParameter()
        parameter.setId("kl")
        parameter.setValue(2.0)
        law.setMath(libsbml.parseL3Formula("kl * A"))

    sbml = edit_sbml(model_sbml("species A = 1; J0: A -> ; A"), local)
    document = OdeSystem.from_sbml(sbml).render("markdown")
    assert "| Local parameters |" in document
    assert r"| $\mathrm{J0}_{\mathrm{kl}}$ |" in document
    assert r"v_{\mathrm{J0}} &= \mathrm{J0}_{\mathrm{kl}} \cdot A" in document


def test_ode_in_lines_with_volume(tmp_path: Path) -> None:
    """The ODE of a long sum is in lines, divided by the volume as a factor."""
    reactions = "\n".join(f"J{k}: S -> ; k * S" for k in range(6))
    sbml = model_sbml(f"compartment c = 2; species S in c = 1; k = 1\n{reactions}")
    system = OdeSystem.from_sbml(sbml)
    latex = system.render("latex")
    assert (
        r"\frac{\mathrm{d} S}{\mathrm{d} t} &= \frac{1}{c} \Bigl( "
        r"-v_{\mathrm{J0}} - v_{\mathrm{J1}} - v_{\mathrm{J2}} - v_{\mathrm{J3}} \\"
        "\n"
        r"  &\quad {} - v_{\mathrm{J4}} - v_{\mathrm{J5}} \Bigr)"
    ) in latex
    typst = system.render("typst")
    assert (
        '(dif S)/(dif t) &= (1)/(c) lr(size: #150%, \\() -v_("J0") - v_("J1") '
        '- v_("J2") - v_("J3") \\\n  & quad "" - v_("J4") - v_("J5") '
        "lr(size: #150%, \\))"
    ) in typst
    compile_typst(typst, tmp_path)


@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
def test_units(fmt: str) -> None:
    """A unit is text with its exponents as superscripts, without ligatures."""
    document = render("demo", fmt)
    expected = {
        "typst": "mole/m#super[3]",
        "latex": r"mole/m\textsuperscript{3}",
        "markdown": "mole/m<sup>3</sup>",
    }
    assert expected[fmt] in document
    repressilator = render("repressilator", fmt)
    expected = {
        "typst": "#text(ligatures: false)[fl]",
        "latex": r"f\kern0pt{}l",
        "markdown": "| fl |",
    }
    assert expected[fmt] in repressilator


def test_notes_are_paragraphs() -> None:
    """The notes of the model are paragraphs of escaped text."""
    document = render("demo", "markdown")
    assert "\n\nThis is a demonstration model in SBML format.\n\n" in document
    assert "koenigmx@hu-berlin.de" in document


@pytest.mark.parametrize("fmt", sorted(SUFFIXES))
def test_negative_exponent_of_a_unit(fmt: str) -> None:
    """The minus of a negative exponent is the minus sign, not a hyphen."""
    context = DocumentContext(OdeSystem.from_sbml(MODELS["events"]), fmt, "id")
    expected = {
        "typst": "s#super[\u22121]",
        "latex": r"s\textsuperscript{\textminus{}1}",
        "markdown": "s<sup>\u22121</sup>",
    }
    assert context.unit("s^-1") == expected[fmt]


def test_tables_without_names_are_compact() -> None:
    """A table whose rows have no name has no name column and its natural width."""
    typst = render("events", "typst")
    compartments = typst[typst.index("= Compartments") : typst.index("= Species")]
    assert "columns: (auto, auto, auto, auto)" in compartments
    assert "[*Name*]" not in compartments
    latex = render("events", "latex")
    compartments = latex[latex.index("{Compartments}") : latex.index("{Species}")]
    assert r"\begin{longtable}[l]{@{}l l l c@{}}" in compartments
    assert r"\textbf{Name}" not in compartments
    markdown = render("events", "markdown")
    assert "| Symbol | Id | Size | Constant |" in markdown
    # a name wraps in the width the other columns leave
    species = latex[latex.index("{Species}") : latex.index("{Parameters}")]
    assert r"\begin{xltabular}{\linewidth}" in species
    assert r"\textbf{Name}" in species


def test_event_assignment_is_one_relation() -> None:
    """`:=` is one relation in every format."""
    assert "S &colon.eq 10" in render("events", "typst")
    assert r"S &\mathrel{:=} 10" in render("events", "markdown")
