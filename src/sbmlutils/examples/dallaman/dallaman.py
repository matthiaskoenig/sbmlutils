"""DallaMan2006."""

from pathlib import Path

from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples import templates
from sbmlutils.factory import *


class U(Units):
    """UnitDefinitions."""

    kg = UnitDefinition("kg")
    mg = UnitDefinition("mg")
    m2 = UnitDefinition("m2", "m^2")
    m3 = UnitDefinition("m3", "m^3")
    min = UnitDefinition("min", "min")
    per_min = UnitDefinition("per_min", "1/min")
    per_mg = UnitDefinition("per_mg", "1/mg")
    l_per_kg = UnitDefinition("l_per_kg", "l/kg")
    dl_per_kg = UnitDefinition("dl_per_kg", "dl/kg")
    mg_per_kg = UnitDefinition("mg_per_kg", "mg/kg")
    mg_per_dl = UnitDefinition("mg_per_dl", "mg/dl")
    mg_per_min = UnitDefinition("mg_per_min", "mg/min")
    pmol_per_kg = UnitDefinition("pmol_per_kg", "pmol/kg")
    pmol_per_l = UnitDefinition("pmol_per_l", "pmol/l")
    pmol_per_lmin = UnitDefinition("pmol_per_lmin", "pmol/l/min")
    pmol_per_kgmin = UnitDefinition("pmol_per_kgmin", "pmol/kg/min")
    pmol_per_kgmin2 = UnitDefinition("pmol_per_kgmin2", "pmol/kg/min^2")
    minkg_per_pmol = UnitDefinition("minkg_per_pmol", "min*kg/pmol")
    mg_per_kgmin = UnitDefinition("mg_per_kgmin", "mg/kg/min")
    mgl_per_kgminpmol = UnitDefinition("mgl_per_kgminpmol", "mg*l/kg/min/pmol")
    mg_per_minpmol = UnitDefinition("mg_per_minpmol", "mg/min/pmol")
    pmolmg_per_kgdl = UnitDefinition("pmolmg_per_kgdl", "pmol*mg/kg/dl")
    pmolmg_per_kgmindl = UnitDefinition("pmolmg_per_kgmindl", "pmol*mg/kg/min/dl")
    pmoldl_per_kgmg = UnitDefinition("pmoldl_per_kgmg", "pmol*dl/kg/mg")
    pmoldl_per_kgminmg = UnitDefinition("pmoldl_per_kgminmg", "pmol*dl/kg/min/mg")


# -------------------------------------------------------------------------------------
# Model
# -------------------------------------------------------------------------------------
_m = Model(
    sid="DallaMan2006",
    name="DallaMan2006",
    notes="""
    <h1>DallaMan2006 - Glucose Insulin System</h1>
    <h2>Description</h2>
    <p>
        This is a A simulation model of the glucose-insulin system in the postprandial state in
        <a href="http://sbml.org">SBML</a> format.
    </p>
    <p>This model is described in the article:</p>
    <div class="bibo:title">
        <a href="http://identifiers.org/pubmed/17926672" title="Access to this publication">Meal simulation model of
        the glucose-insulin system.</a>
    </div>
    <div class="bibo:authorList">Dalla Man C, Rizza RA, Cobelli C.</div>
    <div class="bibo:Journal">IEEE Trans Biomed Eng. 2007 Oct;54(10):1740-9.</div>
    <p>Abstract:</p>
    <div class="bibo:abstract">
    <p>A simulation model of the glucose-insulin system in the
    postprandial state can be useful in several circumstances, including
    testing of glucose sensors, insulin infusion alg"orithms and decision
    support systems for diabetes. Here, we present a new simulation
    model in normal humans that describes the physiological events
    that occur after a meal, by employing the quantitative knowledge
    that has become available in recent years. Model parameters were
    set to fit the mean data of a large normal subject database that underwent
    a triple tracer meal protocol which provided quasi-model independent
    estimates of major glucose and insulin fluxes, e.g., meal
    rate of appearance, endogenous glucose production, utilization of
    glucose, insulin secretion.</p>
    </div>
    """
    + templates.terms_of_use,
    creators=templates.creators,
    model_units=ModelUnits(
        time=U.min,
        extent=U.mole,
        substance=U.mole,
        length=U.meter,
        area=U.m2,
        volume=U.m3,
    ),
    units=U,
)

# -------------------------------------------------------------------------------------
# Parameters
# -------------------------------------------------------------------------------------
_m.parameters = [
    # state variables (initial values)
    Parameter(
        "Gp", 178, U.mg_per_kg, constant=False, name="glucose mass in plasma [mg/kg]"
    ),
    Parameter(
        "Gt",
        135,
        U.mg_per_kg,
        constant=False,
        name="glucose mass rapidly equilibrating tissue [mg/kg]",
    ),
    Parameter(
        "Il", 4.5, U.pmol_per_kg, constant=False, name="insulin mass liver [pmol/kg]"
    ),
    Parameter(
        "Ip", 1.25, U.pmol_per_kg, constant=False, name="insulin mass plasma [pmol/kg]"
    ),
    Parameter(
        "Qsto1", 78000, U.mg, constant=False, name="glucose in the stomach solid [mg]"
    ),
    Parameter(
        "Qsto2", 0, U.mg, constant=False, name="glucose in the stomach liquid [mg]"
    ),
    Parameter("Qgut", 0, U.mg, constant=False, name="glucose in the intestine [mg]"),
    Parameter("I1", 25, U.pmol_per_l, constant=False),  # I1(0) = Ib
    Parameter(
        "Id", 25, U.pmol_per_l, constant=False, name="delayed insulin [pmol/l]"
    ),  # Id(0) = Ib
    Parameter("INS", 0, U.pmol_per_l, constant=False),
    Parameter(
        "Ipo", 3.6, U.pmol_per_kg, constant=False, name="insulin portal vein [pmol/kg]"
    ),
    Parameter("Y", 0, U.pmol_per_kgmin, constant=False, name="Y [pmol/kg/min]"),
]
# rate rules d/dt
_m.rate_rules = [
    RateRule("Gp", "EGP +Ra -U_ii -E -k_1*Gp +k_2*Gt", U.mg_per_kgmin),
    RateRule("Gt", "-U_id + k_1*Gp -k_2*Gt", U.mg_per_kgmin),
    RateRule("Il", "-(m_1+m_3)*Il + m_2*Ip + S", U.pmol_per_kgmin),
    RateRule("Ip", "-(m_2+m_4)*Ip + m_1*Il", U.pmol_per_kgmin),
    RateRule(
        "Qsto1",
        "-k_gri * Qsto1",
        U.mg_per_min,
        name="rate glucose in the stomach solid [mg/min]",
    ),
    RateRule(
        "Qsto2",
        "-k_empt*Qsto2 + k_gri*Qsto1",
        U.mg_per_min,
        name="rate glucose in the stomach liquid [mg/min]",
    ),
    RateRule(
        "Qgut",
        "-k_abs*Qgut + k_empt*Qsto2",
        U.mg_per_min,
        name="rate glucose in the intestine [mg/min]",
    ),
    RateRule("I1", "-k_i*(I1-I)", U.pmol_per_lmin),
    RateRule(
        "Id",
        "-k_i*(Id-I1)",
        U.pmol_per_lmin,
        name="rate delayed insulin signal realized with chain [pmol/l]",
    ),
    RateRule("INS", "(-p_2U*INS) + p_2U*(I-I_b)", U.pmol_per_lmin),
    RateRule(
        "Ipo",
        "(-gamma*Ipo) + S_po",
        U.pmol_per_kgmin,
        name="insulin in the portal vein [pmol/kg]",
    ),
    RateRule(
        "Y", "- alpha * (Y-beta*(G-G_b))", U.pmol_per_kgmin2
    ),  # [1/min] [pmol/kg/min]
    #  beta = (pmol_dl)/(kg*min*mg)     [mg/dl]
]


_m.parameters.extend(
    [
        Parameter("BW", 78, U.kg, name="body weight [kg]"),
        Parameter("D", 78000, U.mg, name="amount of ingested glucose [mg]"),
        # Glucose Kinetics
        Parameter(
            "V_G", 1.88, U.dl_per_kg, name="V_G distribution volume glucose [dl/kg]"
        ),
        Parameter("k_1", 0.065, U.per_min, name="k_1 glucose kinetics"),
        Parameter("k_2", 0.079, U.per_min, name="k_2 glucose kinetics [1/min]"),
        Parameter("G_b", 95, U.mg_per_dl, name="basline plasma glucose [mg/dl]"),
        # Insulin kinetics
        Parameter("V_I", 0.05, U.l_per_kg, name="V_I distribution volume insulin"),
        Parameter("m_1", 0.190, U.per_min),
        Parameter("m_2", 0.484, U.per_min),
        Parameter("m_4", 0.194, U.per_min),
        Parameter("m_5", 0.0304, U.minkg_per_pmol),
        Parameter("m_6", 0.6471, U.dimensionless),
        # Parameter("HE_b", 0.60, U.dimensionless),
        Parameter("I_b", 25, U.pmol_per_l),
        Parameter("S_b", 1.8, U.pmol_per_kgmin),
        # Rate of appearance
        Parameter("k_max", 0.0558, U.per_min),
        Parameter("k_min", 0.0080, U.per_min),
        Parameter("k_abs", 0.057, U.per_min, name="rate of intestinal absorption"),
        Parameter("k_gri", 0.0558, U.per_min, name="rate of stomach grinding"),
        Parameter(
            "f",
            0.90,
            U.dimensionless,
            name="fraction of intestinal absorption which appears in plasma",
        ),
        # Parameter('a', 0.00013, U.per_mg),
        Parameter("b", 0.82, U.dimensionless),
        # Parameter('c', 0.00236, U.per_mg, constant=True),
        Parameter("d", 0.010, U.dimensionless),
        # Endogenous production
        Parameter(
            "k_p1",
            2.70,
            U.mg_per_kgmin,
            name="extrapolated EGP at zero glucose and insulin [mg/kg/min]",
        ),
        Parameter("k_p2", 0.0021, U.per_min, name="liver glucose effectiveness"),
        Parameter(
            "k_p3",
            0.009,
            U.mgl_per_kgminpmol,
            name="parameter governing amplitude of insulin action on the liver [(mg*l)/(kg*min*pmol)]",
        ),
        Parameter(
            "k_p4",
            0.0618,
            U.mg_per_minpmol,
            name="parameter governing amplitude of portal insulin action on the liver",
        ),
        Parameter(
            "k_i",
            0.0079,
            U.per_min,
            name="rate parameter accounting for delay between insulin signal and insulin action [1/min]",
        ),
        Parameter(
            "F_cns",
            1,
            U.mg_per_kgmin,
            name="U_ii; glucose uptake by the brain and erythrocytes [mg/min/kg]",
        ),  # F_cns
        Parameter("V_m0", 2.50, U.mg_per_kgmin),
        Parameter("V_mX", 0.047, U.mgl_per_kgminpmol),
        Parameter("K_m0", 225.59, U.mg_per_kg),
        Parameter("V_f0", 2.5, U.mg_per_kgmin),
        Parameter("V_fX", 0.047, U.mgl_per_kgminpmol),
        Parameter("K_f0", 225.59, U.mg_per_kg),
        Parameter("p_2U", 0.0331, U.per_min),
        Parameter("part", 0.20, U.dimensionless),
        # Secretion
        Parameter("K", 2.30, U.pmoldl_per_kgmg),
        Parameter("alpha", 0.050, U.per_min),
        Parameter("beta", 0.11, U.pmoldl_per_kgminmg),
        Parameter("gamma", 0.5, U.per_min),
        # renal excretion
        # Parameter("k_e1", 0.0005, U.per_min),
        # Parameter("k_e2", 339, U.mg_per_kg),
    ]
)

# -------------------------------------------------------------------------------------
# Rules
# -----------------------------------------------------"--------------------------------


# assignment rules
_m.rules = [
    AssignmentRule(
        "aa", "5 dimensionless / 2 dimensionless /(1 dimensionless - b)/D", U.per_mg
    ),
    AssignmentRule("cc", "5 dimensionless / 2 dimensionless / d / D", U.per_mg),
    AssignmentRule(
        "EGP",
        "k_p1 -k_p2*Gp -k_p3*Id -k_p4*Ipo",
        U.mg_per_kgmin,
        name="EGP endogenous glucose production [mg/kg/min]",
    ),
    AssignmentRule(
        "V_mmax", "(1 dimensionless - part)*(V_m0+V_mX*INS)", U.mg_per_kgmin
    ),
    AssignmentRule("V_fmax", "part*(V_f0 + V_fX*INS)", U.mg_per_kgmin),
    AssignmentRule("E", "0 mg_per_kgmin", U.mg_per_kgmin, name="E renal excretion"),
    AssignmentRule("S", "gamma*Ipo", U.pmol_per_kgmin, name="S insulin secretion"),
    AssignmentRule("I", "Ip/V_I", U.pmol_per_l, name="I plasma insulin concentration"),
    AssignmentRule("G", "Gp/V_G", U.mg_per_dl, name="G plasma glucose concentration"),
    AssignmentRule(
        "HE", "-m_5*S + m_6", U.dimensionless, name="HE hepatic extraction insulin"
    ),
    AssignmentRule("m_3", "HE * m_1/(1 dimensionless - HE)", U.per_min),
    AssignmentRule("Q_sto", "Qsto1 + Qsto2", U.mg, name="glucose in the stomach [mg]"),
    AssignmentRule(
        "Ra",
        "1.32 dimensionless * f * k_abs * Qgut/BW",
        U.mg_per_kgmin,
        name="Ra glucose rate of appearance",
    ),
    AssignmentRule(
        "k_empt",
        "k_min + (k_max-k_min)/2 dimensionless*(tanh(aa*(Q_sto-b*D)) - tanh(cc*(Q_sto-d*D))+2 dimensionless)",
        U.per_min,
        name="rate of gastric emptying",
    ),
    AssignmentRule("U_idm", "V_mmax*Gt/(K_m0+Gt)", U.mg_per_kgmin),
    AssignmentRule("U_idf", "V_fmax*Gt/(K_f0+Gt)", U.mg_per_kgmin),
    AssignmentRule(
        "U_id",
        "U_idm+U_idf",
        U.mg_per_kgmin,
        name="insulin dependent glucose utilization",
    ),
    AssignmentRule(
        "U_ii", "F_cns", U.mg_per_kgmin, name="insulin independent glucose utilization"
    ),
    AssignmentRule(
        "U",
        "U_ii + U_id",
        U.mg_per_kgmin,
        name="U glucose uptake",
        notes="""
    Sum of insulin independent Uii and insulin-dependent glucose utilizations""",
    ),
    AssignmentRule(
        "S_po",
        "Y + K*(EGP +Ra -E -U_ii -k_1*Gp +k_2*Gt)/V_G + S_b",
        U.pmol_per_kgmin,
        name="[pmol/kg/min]",
    ),
]

dallaman_model = _m


def create(output_dir: Path) -> FactoryResult:
    """Create model."""
    return create_model(
        model=dallaman_model,
        filepath=output_dir / f"{dallaman_model.sid}.xml",
        validation_options=ValidationOptions(units_consistency=True),
        sbml_level=3,
        sbml_version=2,
    )


if __name__ == "__main__":
    result: FactoryResult = create(output_dir=Path(__file__).parent / "results")
    visualize_sbml(result.sbml_path)
