"""DallaMan2006."""
# TODO: encode units for model
# TODO: T2DM simulations (in current version not working)

from sbmlutils.examples import templates
from sbmlutils.factory import *
from sbmlutils.units import *


# ---------------------------------------------------------------------------------------------------------------------
mid = "DallaMan2006"
version = 3
notes = Notes(
    [
        """
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
    <p>Asimulation model of the glucose-insulin system in the
postprandial state can be useful in several circumstances, including
testing of glucose sensors, insulin infusion algorithms and decision
support systems for diabetes. Here, we present a new simulation
model in normal humans that describes the physiological events
that occur after a meal, by employing the quantitative knowledge
that has become available in recent years. Model parameters were
set to fit the mean data of a large normal subject database that underwent
a triple tracer meal protocol which provided quasi-modelindependent
estimates of major glucose and insulin fluxes, e.g., meal
rate of appearance, endogenous glucose production, utilization of
glucose, insulin secretion.</p>
    </div>
    """,
        templates.terms_of_use,
    ]
)
creators = templates.creators

# ---------------------------------------------------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------------------------------------------------
model_units = ModelUnits(
    time=UNIT_min,
    extent=UNIT_KIND_MOLE,
    substance=UNIT_KIND_MOLE,
    length=UNIT_m,
    area=UNIT_m2,
    volume=UNIT_m3,
)
units = [
    Unit("kg", [(UNIT_KIND_KILOGRAM, 1.0)]),
    Unit("m", [(UNIT_KIND_METRE, 1.0)]),
    Unit("m2", [(UNIT_KIND_METRE, 2.0)]),
    Unit("m3", [(UNIT_KIND_METRE, 3.0)]),
    Unit("min", [(UNIT_KIND_SECOND, 1.0, 0, 60)]),
    Unit("per_min", [(UNIT_KIND_SECOND, -1.0, 0, 60)]),
    Unit("l_per_kg", [(UNIT_KIND_LITRE, 1.0), (UNIT_KIND_KILOGRAM, -1.0)]),
    Unit("dl_per_kg", [(UNIT_KIND_LITRE, 1.0, -1, 1.0), (UNIT_KIND_KILOGRAM, -1.0)]),
    Unit("mg_per_kg", [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_KILOGRAM, -1.0)]),
    Unit(
        "mg_per_dl", [(UNIT_KIND_GRAM, 1.0, -3, 1.0), (UNIT_KIND_LITRE, -1.0, -1, 1.0)]
    ),
    Unit("pmol_per_kg", [(UNIT_KIND_MOLE, 1.0, -9, 1.0), (UNIT_KIND_KILOGRAM, -1.0)]),
    Unit("pmol_per_l", [(UNIT_KIND_MOLE, 1.0, -9, 1.0), (UNIT_KIND_LITRE, -1.0)]),
    Unit(
        "pmol_per_kgmin",
        [
            (UNIT_KIND_MOLE, 1.0, -9, 1.0),
            (UNIT_KIND_KILOGRAM, -1.0),
            (UNIT_KIND_SECOND, -1.0, 0, 60),
        ],
    ),
    Unit(
        "minkg_per_pmol",
        [
            (UNIT_KIND_SECOND, 1.0, 0, 60),
            (UNIT_KIND_KILOGRAM, 1.0),
            (UNIT_KIND_MOLE, -1.0, -9, 1.0),
        ],
    ),
    Unit(
        "mg_per_kgmin",
        [
            (UNIT_KIND_GRAM, 1.0, -3, 1.0),
            (UNIT_KIND_KILOGRAM, -1.0),
            (UNIT_KIND_SECOND, -1.0, 0, 60),
        ],
    ),
    Unit(
        "mgl_per_kgminpmol",
        [
            (UNIT_KIND_GRAM, 1.0, -3, 1.0),
            (UNIT_KIND_LITRE, 1.0),
            (UNIT_KIND_KILOGRAM, -1.0),
            (UNIT_KIND_SECOND, -1.0, 0, 60),
            (UNIT_KIND_MOLE, -1.0, -9, 1.0),
        ],
    ),
    Unit(
        "mg_per_minpmol",
        [
            (UNIT_KIND_GRAM, 1.0, -3, 1.0),
            (UNIT_KIND_SECOND, -1.0, 0, 60),
            (UNIT_KIND_MOLE, -1.0, -9, 1.0),
        ],
    ),
    Unit(
        "pmolmg_per_kgdl",
        [
            (UNIT_KIND_MOLE, 1.0, -9, 1.0),
            (UNIT_KIND_GRAM, 1.0, -3, 1.0),
            (UNIT_KIND_KILOGRAM, -1.0),
            (UNIT_KIND_LITRE, -1.0, -1, 1.0),
        ],
    ),
    Unit(
        "pmolmg_per_kgmindl",
        [
            (UNIT_KIND_MOLE, 1.0, -9, 1.0),
            (UNIT_KIND_GRAM, 1.0, -3, 1.0),
            (UNIT_KIND_KILOGRAM, -1.0),
            (UNIT_KIND_LITRE, -1.0, -1, 1.0),
            (UNIT_KIND_SECOND, -1.0, 0, 60),
        ],
    ),
]

parameters = [
    # state variables (initial values)
    Parameter("Gp", 178, "mg_per_kg", constant=False, name="glucose plasma"),
    Parameter("Gt", 135, "mg_per_kg", constant=False, name="glucose tissue"),
    Parameter("Il", 4.5, "pmol_per_kg", constant=False, name="insulin mass liver"),
    Parameter("Ip", 1.25, "pmol_per_kg", constant=False, name="insulin mass plasma"),
    Parameter("Qsto1", 78000, "?", constant=False),
    Parameter("Qsto2", 0, "?", constant=False),
    Parameter("Qgut", 0, "?", constant=False),
    Parameter("I1", 25, "?", constant=False),
    Parameter("Id", 25, "pmol_per_l", constant=False, name="delayed insulin"),
    Parameter("INS", 0, "?", constant=False),
    Parameter("Ipo", 3.6, "pmol_per_kg", constant=False, name="insulin portal vein"),
    Parameter("Y", 0, "?", constant=False),
    # bodyweight
    Parameter("BW", 78, "kg", constant=True, name="body weight"),
    Parameter("D", 78000, "?", constant=True),
    # Glucose Kinetics
    Parameter(
        "V_G", 1.88, "dl_per_kg", constant=True, name="V_G distribution volume glucose"
    ),
    Parameter("k_1", 0.065, "per_min", constant=True, name="k_1 glucose kinetics"),
    Parameter("k_2", 0.079, "per_min", constant=True, name="k_2 glucose kinetics"),
    Parameter("G_b", 95, "?", constant=True),
    # Insulin kinetics
    Parameter(
        "V_I", 0.05, "l_per_kg", constant=True, name="V_I distribution volume insulin"
    ),
    Parameter("m_1", 0.190, "per_min", constant=True),
    Parameter("m_2", 0.484, "per_min", constant=True),
    Parameter("m_4", 0.194, "per_min", constant=True),
    Parameter("m_5", 0.0304, "minkg_per_pmol", constant=True),
    Parameter("m_6", 0.6471, "-", constant=True),
    Parameter("HE_b", 0.60, "-", constant=True),
    Parameter("I_b", 25, "?", constant=True),
    Parameter("S_b", 1.8, "?", constant=True),
    # Rate of appearance
    Parameter("k_max", 0.0558, "per_min", constant=True),
    Parameter("k_min", 0.0080, "per_min", constant=True),
    Parameter("k_abs", 0.057, "per_min", constant=True),
    Parameter("k_gri", 0.0558, "per_min", constant=True),
    Parameter("f", 0.90, "-", constant=True),
    # Parameter('a', 0.00013, 'per_mg', constant=True),
    Parameter("b", 0.82, "-", constant=True),
    # Parameter('c', 0.00236, 'per_mg', constant=True),
    Parameter("d", 0.010, "-", constant=True),
    # Endogenous production
    Parameter("k_p1", 2.70, "mg_per_kgmin", constant=True),
    Parameter("k_p2", 0.0021, "per_min", constant=True),
    Parameter("k_p3", 0.009, "mgl_per_kgminpmol", constant=True),
    Parameter("k_p4", 0.0618, "mg_per_minpmol", constant=True),
    Parameter("k_i", 0.0079, "per_min", constant=True),
    # Utilization
    Parameter(
        "U_ii",
        1,
        "mg_per_kgmin",
        constant=True,
        name="insulin independent glucose utilization",
    ),  # F_cns
    Parameter("V_m0", 2.50, "mg_per_kgmin", constant=True),
    Parameter("V_mX", 0.047, "mgl_per_kgminpmol", constant=True),
    Parameter("K_m0", 225.59, "mg_per_kg", constant=True),
    Parameter("V_f0", 2.5, "mg_per_kgmin", constant=True),
    Parameter("V_fX", 0.047, "mgl_per_kgminpmol", constant=True),
    Parameter("K_f0", 225.59, "mg_per_kg", constant=True),
    Parameter("p_2U", 0.0331, "per_min", constant=True),
    Parameter("part", 0.20, "?", constant=True),
    # Secretion
    Parameter("K", 2.30, "pmolmg_per_kgdl", constant=True),
    Parameter("alpha", 0.050, "per_min", constant=True),
    Parameter("beta", 0.11, "pmolmg_per_kgmindl", constant=True),
    Parameter("gamma", 0.5, "per_min", constant=True),
    # renal excretion
    Parameter("k_e1", 0.0005, "per_min", constant=True),
    Parameter("k_e2", 339, "mg_per_kg", constant=True),
]

# ---------------------------------------------------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------------------------------------------------
rate_rules = [
    # rate rules d/dt
    RateRule("Gp", "EGP +Ra -U_ii -E -k_1*Gp +k_2*Gt", "mg_per_kgmin"),
    RateRule("Gt", "-U_id + k_1*Gp -k_2*Gt", "mg_per_kgmin"),
    RateRule("Il", "-(m_1+m_3)*Il + m_2*Ip + S", "pmol_per_kg"),
    RateRule("Ip", "-(m_2+m_4)*Ip + m_1*Il", "pmol_per_kg"),
    RateRule("Qsto1", "-k_gri*Qsto1", "?"),
    RateRule("Qsto2", "(-k_empt*Qsto2)+k_gri*Qsto1", "?"),
    RateRule("Qgut", "(-k_abs*Qgut)+k_empt*Qsto2", "?"),
    RateRule("I1", "-k_i*(I1-I)", "?"),
    RateRule("Id", "-k_i*(Id-I1)", "?"),
    RateRule("INS", "(-p_2U*INS)+p_2U*(I-I_b)", "?"),
    RateRule("Ipo", "(-gamma*Ipo)+S_po", "?"),
    RateRule("Y", "-alpha*(Y-beta*(G-G_b))", "?"),
]

rules = [
    AssignmentRule("aa", "5/2/(1-b)/D", "?"),
    AssignmentRule("cc", "5/2/d/D", "?"),
    AssignmentRule(
        "EGP",
        "k_p1-k_p2*Gp-k_p3*Id-k_p4*Ipo",
        "mg_per_kgmin",
        name="EGP endogenous glucose production",
    ),
    AssignmentRule("V_mmax", "(1-part)*(V_m0+V_mX*INS)", "?"),
    AssignmentRule("V_fmax", "part*(V_f0+V_fX*INS)", "?"),
    AssignmentRule("E", "0", "mg_per_kgmin", "renal excretion"),
    AssignmentRule("S", "gamma*Ipo", "pmol_per_kgmin", name="S insulin secretion"),
    AssignmentRule("I", "Ip/V_I", "pmol_per_l", name="I plasma insulin"),
    AssignmentRule("G", "Gp/V_G", "mg_per_dl", name="G plasma Glucose"),
    AssignmentRule("HE", "-m_5*S + m_6", "-", name="HE hepatic extraction insulin"),
    AssignmentRule("m_3", "HE*m_1/(1-HE)", "per_min"),
    AssignmentRule("Q_sto", "Qsto1+Qsto2", "?"),
    AssignmentRule(
        "Ra",
        "1.32 dimensionless*f*k_abs*Qgut/BW",
        "mg_per_kgmin",
        name="Ra glucose rate of appearance",
    ),
    # % Ra', f*k_abs*Qgut/BW
    AssignmentRule(
        "k_empt",
        "k_min+(k_max-k_min)/2*(tanh(aa*(Q_sto-b*D))-tanh(cc*(Q_sto-d*D))+2)",
        "?",
    ),
    AssignmentRule("U_idm", "V_mmax*Gt/(K_m0+Gt)", "mg_per_kgmin"),
    AssignmentRule("U_idf", "V_fmax*Gt/(K_f0+Gt)", "mg_per_kgmin"),
    AssignmentRule(
        "U_id",
        "U_idm+U_idf",
        "mg_per_kgmin",
        name="insulin dependent glucose utilization",
    ),
    AssignmentRule("U", "U_ii+U_id", "mg_per_kgmin", name="U glucose uptake"),
    AssignmentRule("S_po", "Y+K*(EGP+Ra-E-U_ii-k_1*Gp+k_2*Gt)/V_G+S_b", "?"),
]
