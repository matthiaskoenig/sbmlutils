"""Test the analysis of an SBML model into its ODE system."""

from pathlib import Path

import libsbml
import pytest
from ode_helpers import edit_sbml, model_sbml

from sbmlutils.converters.ode.dependencies import names, order
from sbmlutils.converters.ode.events import trigger_root
from sbmlutils.converters.ode.system import Assignment, Ode, OdeSystem, Participant
from sbmlutils.resources import COMP_ICG_BODY, DEMO_SBML, MODELS_DIR


def formula(ast: libsbml.ASTNode | None) -> str:
    """Infix formula of the math, as libsbml writes it."""
    assert ast is not None
    return str(libsbml.formulaToL3String(ast))


def parse(text: str) -> libsbml.ASTNode:
    """Math of an infix formula."""
    ast = libsbml.parseL3Formula(text)
    assert ast is not None, libsbml.getLastParseL3Error()
    return ast


def odes(system: OdeSystem) -> dict[str, Ode]:
    """The odes of the system by their state."""
    return {ode.variable: ode for ode in system.odes}


def math_of(assignments: tuple[Assignment, ...]) -> dict[str, tuple[str, str]]:
    """The formula and the origin of each assignment by its variable."""
    return {a.variable: (formula(a.math), a.origin) for a in assignments}


def system_of(antimony: str) -> OdeSystem:
    """The ODE system of a model written in antimony."""
    return OdeSystem.from_sbml(model_sbml(antimony))


# --- odes -----------------------------------------------------------------------------


def test_reaction_ode_in_concentration() -> None:
    """The reaction terms of a species in concentration are divided by its volume."""
    system = system_of("""
        compartment c = 2; species S1 in c = 10; species S2 in c = 0
        J0: S1 -> 2 S2; k*S1; k = 0.1
    """)
    assert system.states == ("S1", "S2")
    ode = odes(system)
    assert formula(ode["S2"].rhs) == "2 * J0 / c"
    assert formula(ode["S1"].rhs) == "-J0 / c"
    assert formula(ode["S1"].reaction_terms) == "-J0"
    assert ode["S1"].volume == "c"
    assert ode["S1"].origin == "reactions"
    assert ode["S1"].amount_of is None
    reaction = system.reactions[0]
    assert reaction.reactants == (Participant("S1", 1.0),)
    assert reaction.products == (Participant("S2", 2.0),)
    assert formula(reaction.rate) == "k * S1"
    assert system.constants == ("c", "k")
    assert system.assigned == ("J0",)
    assert math_of(system.assignments) == {"J0": ("k * S1", "reaction")}
    assert system.unsupported == ()


def test_reaction_ode_in_amount() -> None:
    """The reaction terms of a species in amount are not divided, a sum keeps signs."""
    system = system_of("""
        compartment c = 2; substanceOnly species S in c = 10
        J0: -> S; 1; J1: S -> ; k*S; k = 0.1
    """)
    ode = odes(system)
    assert formula(ode["S"].rhs) == "J0 + -J1"
    assert ode["S"].volume is None
    assert system.quantity("S").amount


def test_boundary_and_constant_species_are_not_states() -> None:
    """A boundary or constant species is a constant, so is a species of no reaction."""
    system = system_of("""
        compartment c = 1; species $B in c = 1; const species K in c = 2
        species S in c = 0; species U in c = 3
        J0: B -> S; k*B*K; k = 0.1
    """)
    assert system.states == ("S",)
    assert system.constants == ("c", "B", "K", "U", "k")
    assert system.quantity("B").boundary


def test_reaction_without_kinetic_law_has_rate_zero() -> None:
    """A reaction without a kinetic law has the rate 0, as roadrunner holds it."""
    sbml = edit_sbml(
        model_sbml("compartment c = 1; species S in c = 10; J0: S -> ; 1"),
        lambda model: model.getReaction("J0").unsetKineticLaw(),
    )
    system = OdeSystem.from_sbml(sbml)
    assert formula(system.reactions[0].rate) == "0"
    assert system.unsupported == ()


def test_variable_compartment_ode() -> None:
    """A species in concentration in a variable compartment is integrated as amount."""
    system = system_of("""
        compartment c = 2; c' = 0.1; species S in c = 10
        J0: S -> ; k*S; k = 0.1
    """)
    assert system.states == ("c", "n_S")
    ode = odes(system)
    assert ode["n_S"].amount_of == "S"
    assert formula(ode["n_S"].rhs) == "-J0"
    assert ode["n_S"].volume is None
    assert formula(ode["c"].rhs) == "0.1"
    assert ode["c"].origin == "rate_rule"
    amount = system.quantity("n_S")
    assert amount.amount_of == "S"
    assert amount.role == "state"
    assert amount.compartment == "c"
    assert amount.symbol.kind == "species"
    assert system.symbol("n_S").name == "amount of S"
    assert system.quantity("S").role == "assigned"
    assert math_of(system.assignments) == {
        "S": ("n_S / c", "concentration"),
        "J0": ("k * S", "reaction"),
    }
    assert system.assigned == ("S", "J0")
    assert math_of(system.initial) == {
        "c": ("2", "initial_value"),
        "S": ("10", "initial_value"),
        "n_S": ("S * c", "initial_value"),
    }
    assert [a.variable for a in system.initial] == ["c", "S", "n_S"]


def test_variable_compartment_initial_amount() -> None:
    """The amount of a species with an initial amount is the initial amount."""

    def initial_amount(model: libsbml.Model) -> None:
        species: libsbml.Species = model.getSpecies("S")
        species.unsetInitialConcentration()
        species.setInitialAmount(20)

    sbml = edit_sbml(
        model_sbml(
            "compartment c = 2; c := 2 + time; species S in c = 10; J0: S -> ; k*S; k = 0.1"
        ),
        initial_amount,
    )
    system = OdeSystem.from_sbml(sbml)
    assert system.states == ("n_S",)
    assert system.quantity("n_S").value == 20.0
    assert system.quantity("S").value is None
    assert math_of(system.initial) == {
        "c": ("2 + time", "assignment_rule"),
        "n_S": ("20", "initial_value"),
        "S": ("n_S / c", "concentration"),
    }


def test_variable_compartment_keeps_the_amount_of_a_constant_species() -> None:
    """A species of no reaction in a variable compartment keeps its amount."""
    system = system_of("""
        compartment c = 2; c' = 1; species $B in c = 10
    """)
    assert system.states == ("c",)
    assert system.quantity("n_B").role == "constant"
    assert "n_B" in system.constants
    assert math_of(system.assignments) == {"B": ("n_B / c", "concentration")}
    assert math_of(system.initial)["n_B"] == ("B * c", "initial_value")


def test_amount_id_is_unique() -> None:
    """The id of an amount is made unique against the ids of the model."""
    system = system_of("""
        compartment c = 2; c' = 1; species S in c = 10; n_S = 1
    """)
    assert system.quantity("n_S_1").amount_of == "S"


def test_local_parameter_is_renamed() -> None:
    """A local parameter becomes a global constant `<reaction>_<id>`, made unique."""

    def local_parameter(model: libsbml.Model) -> None:
        law: libsbml.KineticLaw = model.getReaction("J0").getKineticLaw()
        parameter: libsbml.LocalParameter = law.createLocalParameter()
        parameter.setId("k")
        parameter.setValue(0.2)
        parameter.setName("rate constant")

    sbml = edit_sbml(
        model_sbml("""
            compartment c = 1; species S in c = 10
            J0: S -> ; k*S; k = 0.1; J0_k = 5
        """),
        local_parameter,
    )
    system = OdeSystem.from_sbml(sbml)
    reaction = system.reactions[0]
    assert reaction.local_parameters == ("J0_k_1",)
    assert formula(reaction.rate) == "J0_k_1 * S"
    local = system.quantity("J0_k_1")
    assert local.value == 0.2
    assert local.role == "constant"
    assert local.symbol.name == "rate constant"
    assert [p.symbol.sid for p in system.parameters] == ["k", "J0_k", "J0_k_1"]
    assert system.quantity("k").value == 0.1


def test_conversion_factor() -> None:
    """The conversion factor of a species, else of the model, multiplies its terms."""

    def factors(model: libsbml.Model) -> None:
        model.getSpecies("S1").setConversionFactor("f1")
        model.setConversionFactor("f2")

    sbml = edit_sbml(
        model_sbml("""
            compartment c = 1; species S1 in c = 10; species S2 in c = 0
            J0: S1 -> 2 S2; k*S1; k = 0.1; f1 = 3; f2 = 4
        """),
        factors,
    )
    system = OdeSystem.from_sbml(sbml)
    ode = odes(system)
    assert formula(ode["S1"].rhs) == "-(f1 * J0) / c"
    assert formula(ode["S2"].rhs) == "2 * f2 * J0 / c"
    assert system.quantity("S1").conversion_factor == "f1"
    assert system.quantity("S2").conversion_factor == "f2"


def test_stoichiometry_math() -> None:
    """A stoichiometry with a rule or an initial assignment is its species reference."""
    system = system_of("""
        compartment c = 1; species S in c = 10; species P in c = 0; k = 0.1
        J0: S -> n P; k*S; n := 1 + time
        J1: S -> m P; k*S; m = 2*k
        J2: S -> q P; k*S; q = 3
    """)
    j0, j1, j2 = system.reactions
    assert j0.products == (Participant("P", "n"),)
    assert j1.products == (Participant("P", "m"),)
    assert j2.products == (Participant("P", 3.0),)
    assert formula(odes(system)["P"].rhs) == "(n * J0 + m * J1 + 3 * J2) / c"
    n = system.quantity("n")
    assert n.symbol.kind == "species_reference"
    assert n.role == "assigned"
    assert system.quantity("m").role == "constant"
    assert system.quantity("q").value == 3.0
    assert math_of(system.assignments)["n"] == ("1 + time", "assignment_rule")
    assert math_of(system.initial)["m"] == ("2 * k", "initial_assignment")
    assert [s.symbol.sid for s in system.species_references] == ["n", "m", "q"]


def test_rate_rule_on_parameter_and_species() -> None:
    """A rate rule is the ode as written, on a parameter, a compartment, a species."""
    system = system_of("""
        compartment c = 2; c' = 0.2; species S in d = 10; compartment d = 3
        species $B in d = 1; p = 1
        p' = 2*p; S' = 0.5; B' = -0.1
    """)
    assert system.states == ("c", "S", "B", "p")
    ode = odes(system)
    assert formula(ode["S"].rhs) == "0.5"
    assert ode["S"].volume is None
    assert ode["S"].reaction_terms is None
    assert {o.origin for o in system.odes} == {"rate_rule"}
    assert formula(ode["p"].rhs) == "2 * p"
    assert formula(ode["B"].rhs) == "-0.1"


def test_rateof_of_state_and_constant() -> None:
    """The rateOf of a state is its right hand side, of a constant 0."""
    system = system_of("""
        compartment c = 2; species S in c = 10
        J0: S -> ; k*S; k = 0.1
        y := rateOf(S) + rateOf(k)
    """)
    assert math_of(system.assignments)["y"] == ("-J0 / c + 0", "assignment_rule")
    assert [a.variable for a in system.assignments] == ["J0", "y"]
    assert system.unsupported == ()


def test_rateof_of_a_concentration_in_a_variable_compartment() -> None:
    """The rateOf of a concentration held as amount is d(n/V)/dt."""
    system = system_of("""
        compartment c = 2; c' = 1; species S in c = 10
        J0: S -> ; k*S; k = 0.1
        y := rateOf(S)
    """)
    assert math_of(system.assignments)["y"] == (
        "(-J0 - S * 1) / c",
        "assignment_rule",
    )


def test_rateof_of_an_assigned_variable_is_unsupported() -> None:
    """The rateOf of an assigned variable would need symbolic differentiation.

    SBML forbids it, libsbml reads it with an error.
    """

    def rule(model: libsbml.Model) -> None:
        rule: libsbml.AssignmentRule = model.createAssignmentRule()
        rule.setVariable("y")
        rule.setMath(parse("rateOf(x)"))

    sbml = edit_sbml(model_sbml("x := 2 * time; var y"), rule)
    system = OdeSystem.from_sbml(sbml)
    assert system.unsupported == (("rateOf of an assigned variable", "y"),)


def test_assignment_order_and_cycle() -> None:
    """Assignments are in the order of their dependencies, a cycle is an error."""
    system = system_of("""
        compartment c = 1; species S in c = 0
        a := b + 1; b := 2 * time; J0: -> S; a
    """)
    assert [a.variable for a in system.assignments] == ["b", "a", "J0"]
    assert system.assigned == ("b", "a", "J0")

    def cycle(model: libsbml.Model) -> None:
        for variable, text in (("a", "b + 1"), ("b", "2 * a")):
            rule: libsbml.AssignmentRule = model.createAssignmentRule()
            rule.setVariable(variable)
            rule.setMath(parse(text))

    sbml = edit_sbml(model_sbml("var a; var b"), cycle)
    with pytest.raises(ValueError, match=r"\['a', 'b'\] depend on each other"):
        OdeSystem.from_sbml(sbml)


def test_initial_assignment_depends_on_rule() -> None:
    """An initial assignment of a rule and a rule of an initial assignment (#438)."""
    system = system_of("""
        compartment c = 1; species S in c; S = x; x := 2 * k; k = 3
        p = 5 * k; y := p + 1
        J0: S -> ; k*S
    """)
    initial = math_of(system.initial)
    assert initial == {
        "S": ("x", "initial_assignment"),
        "p": ("5 * k", "initial_assignment"),
        "x": ("2 * k", "assignment_rule"),
        "y": ("p + 1", "assignment_rule"),
    }
    sequence = [a.variable for a in system.initial]
    assert sequence.index("x") < sequence.index("S")
    assert sequence.index("p") < sequence.index("y")


def test_initial_value_needs_a_reaction_rate() -> None:
    """A reaction rate is computed at t=0 if an initial value depends on it."""
    system = system_of("""
        compartment c = 1; species S in c = 10; J0: S -> ; k*S; k = 0.1
        p = J0 * 2
    """)
    assert [a.variable for a in system.initial] == ["S", "J0", "p"]
    assert math_of(system.initial)["J0"] == ("k * S", "reaction")


def test_initial_amount_with_compartment_from_initial_assignment() -> None:
    """An initial amount is divided by the initial size, from an initial assignment."""

    def initial_amount(model: libsbml.Model) -> None:
        species: libsbml.Species = model.getSpecies("S")
        species.unsetInitialConcentration()
        species.setInitialAmount(12)

    sbml = edit_sbml(
        model_sbml("""
            compartment c; c = 2 * k; k = 3; species S in c = 1; J0: S -> ; k*S
        """),
        initial_amount,
    )
    system = OdeSystem.from_sbml(sbml)
    assert system.quantity("S").value is None
    initial = math_of(system.initial)
    assert initial["S"] == ("12 / c", "initial_value")
    assert initial["c"] == ("2 * k", "initial_assignment")
    assert [a.variable for a in system.initial] == ["c", "S"]
    assert system.constants == ("c", "k")


def test_initial_concentration_of_species_in_amount() -> None:
    """An initial concentration of a species in amount is multiplied by the size."""

    def concentration(model: libsbml.Model) -> None:
        species: libsbml.Species = model.getSpecies("S")
        species.unsetInitialAmount()
        species.setInitialConcentration(3)

    sbml = edit_sbml(
        model_sbml("""
            compartment c = 2; substanceOnly species S in c = 3; J0: S -> ; k*S; k = 1
        """),
        concentration,
    )
    system = OdeSystem.from_sbml(sbml)
    assert math_of(system.initial) == {"S": ("3 * c", "initial_value")}


def test_unsupported_constructs_are_collected() -> None:
    """Algebraic rules and delay are collected in the order of the document."""
    system = system_of("""
        compartment c = 1; species S in c = 10; x = 1; y = 2
        0 = x + y - 3
        z := delay(S, 1)
    """)
    assert system.unsupported == (("delay", "z"), ("algebraic rule", "_alg0"))


def test_fast_reaction_is_unsupported() -> None:
    """A fast reaction (L3V1) is unsupported, a rule without id has its position."""
    sbml = edit_sbml(
        model_sbml("""
            compartment c = 1; species S in c = 10; x = 1; y = 2; 0 = x + y - 3
            J0: S -> ; k*S; k = 0.1
        """),
        lambda model: model.getReaction("J0").setFast(True),
        level=(3, 1),
    )
    system = OdeSystem.from_sbml(sbml)
    assert system.info.version == 1
    assert system.unsupported == (("algebraic rule", "rule0"), ("fast reaction", "J0"))


def test_event_fields_and_root() -> None:
    """The fields of an event and the root function of its trigger."""
    system = system_of("""
        compartment c = 1; species S in c = 10; k = 1
        E1: at 1 after (time > 2 && S < 5), priority=2, t0=false, persistent=false, fromTrigger=false: k = 2, S = 1
    """)
    (event,) = system.events
    assert event.symbol.sid == "E1"
    assert event.symbol.kind == "event"
    assert formula(event.trigger) == "(time > 2) && (S < 5)"
    assert formula(event.root) == "min(time - 2, 5 - S)"
    assert not event.initial_value
    assert not event.persistent
    assert not event.use_values_from_trigger_time
    assert formula(event.delay) == "1"
    assert formula(event.priority) == "2"
    assert {a.variable: formula(a.math) for a in event.assignments} == {
        "k": "2",
        "S": "1",
    }


def test_event_assigns_amount_of_species_in_variable_compartment() -> None:
    """An event sets the amount with the size before the event (test case 01779)."""
    system = system_of("""
        compartment C1 = 0.5; species $S1 in C1 = 2; species R in C1 = 1; R' = 0
        x := S1
        E0: at time >= 0.45: C1 = 0.2, S1 = 0.2
    """)
    (event,) = system.events
    assert {a.variable: formula(a.math) for a in event.assignments} == {
        "C1": "0.2",
        "n_S1": "0.2 * C1",
        "R": "R * C1 / 0.2",
    }


def test_event_without_id_and_trigger() -> None:
    """An event without an id gets one, a missing trigger never fires."""

    def anonymous(model: libsbml.Model) -> None:
        event: libsbml.Event = model.getEvent("E1")
        event.unsetId()
        event.unsetTrigger()

    sbml = edit_sbml(
        model_sbml("k = 1; E1: at time > 1: k = 2"),
        anonymous,
    )
    (event,) = OdeSystem.from_sbml(sbml).events
    assert event.symbol.sid == "event0"
    assert formula(event.trigger) == "false"
    assert formula(event.root) == "-1"


def test_event_assignment_to_a_constant_is_unsupported() -> None:
    """An event cannot change a constant."""
    sbml = edit_sbml(
        model_sbml("k = 1; E1: at time > 1: k = 2"),
        lambda model: model.getParameter("k").setConstant(True),
    )
    system = OdeSystem.from_sbml(sbml)
    assert system.unsupported == (("event assignment to a constant", "E1"),)


def test_event_trigger_with_function_call() -> None:
    """The root of a trigger which calls a function is the root of its body."""
    system = system_of("""
        function lessthan(x, y)
            x < y
        end
        k = 1; E1: at lessthan(k, time): k = 2
    """)
    (event,) = system.events
    assert formula(event.trigger) == "lessthan(k, time)"
    assert formula(event.root) == "time - k"
    assert system.unsupported == ()


def test_rule_without_math_is_ignored() -> None:
    """A rule without math has no effect (L3V2), its variable does not change."""
    sbml = edit_sbml(
        model_sbml("var p = 3"),
        lambda model: model.createRateRule().setVariable("p"),
    )
    system = OdeSystem.from_sbml(sbml)
    assert system.states == ()
    assert system.constants == ("p",)
    assert system.unsupported == ()


def test_event_with_equality_trigger_is_unsupported() -> None:
    """A trigger without a continuous root function is unsupported."""
    system = system_of("k = 1; E1: at time == 1: k = 2")
    assert system.unsupported == (("event trigger", "E1"),)
    assert system.events[0].root is None


@pytest.mark.parametrize(
    ("trigger", "root"),
    [
        ("x > 1", "x - 1"),
        ("x >= 1", "x - 1"),
        ("x < 1", "1 - x"),
        ("x <= 1", "1 - x"),
        ("a > 1 && b < 2", "min(a - 1, 2 - b)"),
        ("a > 1 || b < 2", "max(a - 1, 2 - b)"),
        ("!(x > 1)", "-(x - 1)"),
        ("true", "1"),
        ("false", "-1"),
        ("1 < x < 3", "min(x - 1, 3 - x)"),
        ("xor(a > 1, b > 1)", "max(min(a - 1, -(b - 1)), min(-(a - 1), b - 1))"),
        ("implies(a > 1, b > 1)", "max(-(a - 1), b - 1)"),
        ("(a > 1 && b > 1) || !(c < 1)", "max(min(a - 1, b - 1), -(1 - c))"),
        ("3", "1"),
        ("0", "-1"),
        ("and()", "1"),
        ("or()", "-1"),
        ("xor()", "-1"),
        (
            "xor(a > 1, b > 1, c > 1)",
            "max(min(max(min(a - 1, -(b - 1)), min(-(a - 1), b - 1)), -(c - 1)), "
            "min(-max(min(a - 1, -(b - 1)), min(-(a - 1), b - 1)), c - 1))",
        ),
    ],
)
def test_trigger_root(trigger: str, root: str) -> None:
    """The sign of the root function is the truth value of the trigger."""
    assert formula(trigger_root(parse(trigger))) == root


@pytest.mark.parametrize(
    "trigger", ["x == 1", "x != 1", "b", "piecewise(true, x > 1, false)"]
)
def test_trigger_root_unsupported(trigger: str) -> None:
    """A trigger without a continuous root function raises."""
    with pytest.raises(NotImplementedError):
        trigger_root(parse(trigger))


# --- dependencies ---------------------------------------------------------------------


def test_names() -> None:
    """The identifiers of a math, not its calls, time or the arguments of csymbols."""
    assert names(parse("f(a, b) + time * c - avogadro")) == {"a", "b", "c"}


def test_order_keeps_input_order_on_ties() -> None:
    """The first item which is ready comes first, unknown ids are no edges."""
    items = [
        ("c", parse("b + z")),
        ("a", None),
        ("b", parse("a * 2")),
        ("d", parse("1")),
    ]
    assert order(items) == ["a", "b", "c", "d"]


def test_order_cycle() -> None:
    """A cycle names the variables in it, a self reference too."""
    with pytest.raises(ValueError, match=r"\['a'\] depend on each other in a cycle"):
        order([("a", parse("a + 1"))])
    with pytest.raises(ValueError, match=r"\['b', 'c'\] depend"):
        order(
            [("a", None), ("b", parse("c")), ("c", parse("b + a")), ("d", parse("c"))]
        )


# --- reading --------------------------------------------------------------------------


def test_model_info(tmp_path: Path) -> None:
    """The model information, the source is the name of the file it was read from."""

    def describe(model: libsbml.Model) -> None:
        model.setName("A model")
        model.setTimeUnits("second")
        model.setNotes(
            "<body xmlns='http://www.w3.org/1999/xhtml'><p>Some notes</p></body>"
        )

    sbml = edit_sbml(model_sbml("k = 1"), describe)
    path = tmp_path / "model.xml"
    path.write_text(sbml)
    info = OdeSystem.from_sbml(path).info
    assert info.sid == "__main"
    assert info.name == "A model"
    assert (info.level, info.version) == (3, 2)
    assert info.notes == "Some notes"
    assert info.units["time"] == "s"
    assert info.units["substance"] is None
    assert info.source == "model.xml"
    assert OdeSystem.from_sbml(sbml).info.source is None


def test_symbols_and_quantities() -> None:
    """Every id of the system has a symbol, a quantity is looked up by its id."""
    system = OdeSystem.from_sbml(DEMO_SBML)
    for quantity in system.quantities:
        assert system.quantity(quantity.symbol.sid) is quantity
    for reaction in system.reactions:
        assert system.symbol(reaction.symbol.sid) is reaction.symbol
    with pytest.raises(KeyError):
        system.quantity("unknown")


def test_document_is_not_changed() -> None:
    """A document which is passed is read, the flattening works on a copy."""
    doc: libsbml.SBMLDocument = libsbml.readSBMLFromFile(str(COMP_ICG_BODY))
    OdeSystem.from_sbml(doc)
    assert doc.getModel().getPlugin("comp").getNumSubmodels() == 1


def test_comp_model_is_flattened() -> None:
    """A comp model is flattened before it is analysed."""
    system = OdeSystem.from_sbml(COMP_ICG_BODY)
    flat = OdeSystem.from_sbml(MODELS_DIR / "comp" / "icg_body_flat.xml")
    assert [s.symbol.sid for s in system.species] == [
        s.symbol.sid for s in flat.species
    ]
    assert system.states == flat.states
    assert system.unsupported == ()


def test_invalid_source_raises() -> None:
    """A document without a model is no system."""
    doc = libsbml.SBMLDocument(3, 2)
    with pytest.raises(ValueError, match="no model"):
        OdeSystem.from_sbml(doc)
