"""DallaMan2006."""
# TODO: encode units for model
# TODO: T2DM simulations (in current version not working)

from sbmlutils.examples import templates
from sbmlutils.factory import *


class U(Units):
    """UnitDefinitions."""

    kg = UnitDefinition("kg")
    m2 = UnitDefinition("m2", "m2")
    m3 = UnitDefinition("m3", "m3")
    min = UnitDefinition("min")
    per_min = UnitDefinition("per_min", "1/min")
    l_per_kg = UnitDefinition("l_per_kg", "l/kg")
    dl_per_kg = UnitDefinition("dl_per_kg", "dl/kg")
    mg_per_kg = UnitDefinition("mg_per_kg", "mg/kg")
    mg_per_dl = UnitDefinition("mg_per_dl", "mg/dl")
    pmol_per_kg = UnitDefinition("pmol_per_kg", "pmol/kg")
    pmol_per_l = UnitDefinition("pmol_per_l", "pmol/l")
    pmol_per_kgmin = UnitDefinition("pmol_per_kgmin", "pmol/kg/min")
    minkg_per_pmol = UnitDefinition("minkg_per_pmol", "min*kg/pmol")
    mg_per_kgmin = UnitDefinition("mg_per_kgmin", "mg/kg/min")
    mgl_per_kgminpmol = UnitDefinition("mgl_per_kgminpmol", "mg*l/kg/min/pmol")
    mg_per_minpmol = UnitDefinition("mg_per_minpmol", "mg/min/pmol")
    pmolmg_per_kgdl = UnitDefinition("pmolmg_per_kgdl", "pmol*mg/kg/dl")
    pmolmg_per_kgmindl = UnitDefinition("pmolmg_per_kgmindl", "pmol*mg/kg/min/dl")


_m = Model("DallaMan2006_v4")
_m.notes = (
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
<p>A simulation model of the glucose-insulin system in the
postprandial state can be useful in several circumstances, including
testing of glucose sensors, insulin infusion algorithms and decision
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
    + templates.terms_of_use
)
_m.creators = templates.creators

# ---------------------------------------------------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------------------------------------------------
_m.model_units = ModelUnits(
    time=U.min,
    extent=U.mole,
    substance=U.mole,
    length=U.meter,
    area=U.m2,
    volume=U.m3,
)

_m.parameters = [
    # state variables (initial values)
    Parameter("Gp", 178, U.mg_per_kg, constant=False, name="glucose plasma"),
    Parameter("Gt", 135, U.mg_per_kg, constant=False, name="glucose tissue"),
    Parameter("Il", 4.5, U.pmol_per_kg, constant=False, name="insulin mass liver"),
    Parameter("Ip", 1.25, U.pmol_per_kg, constant=False, name="insulin mass plasma"),
    Parameter("Qsto1", 78000, None, constant=False),
    Parameter("Qsto2", 0, None, constant=False),
    Parameter("Qgut", 0, None, constant=False),
    Parameter("I1", 25, None, constant=False),
    Parameter("Id", 25, U.pmol_per_l, constant=False, name="delayed insulin"),
    Parameter("INS", 0, None, constant=False),
    Parameter("Ipo", 3.6, U.pmol_per_kg, constant=False, name="insulin portal vein"),
    Parameter("Y", 0, None, constant=False),
    # bodyweight
    Parameter("BW", 78, U.kg, constant=True, name="body weight"),
    Parameter("D", 78000, None, constant=True),
    # Glucose Kinetics
    Parameter(
        "V_G", 1.88, U.dl_per_kg, constant=True, name="V_G distribution volume glucose"
    ),
    Parameter("k_1", 0.065, U.per_min, constant=True, name="k_1 glucose kinetics"),
    Parameter("k_2", 0.079, U.per_min, constant=True, name="k_2 glucose kinetics"),
    Parameter("G_b", 95, None, constant=True),
    # Insulin kinetics
    Parameter(
        "V_I", 0.05, U.l_per_kg, constant=True, name="V_I distribution volume insulin"
    ),
    Parameter("m_1", 0.190, U.per_min, constant=True),
    Parameter("m_2", 0.484, U.per_min, constant=True),
    Parameter("m_4", 0.194, U.per_min, constant=True),
    Parameter("m_5", 0.0304, U.minkg_per_pmol, constant=True),
    Parameter("m_6", 0.6471, U.dimensionless, constant=True),
    Parameter("HE_b", 0.60, U.dimensionless, constant=True),
    Parameter("I_b", 25, None, constant=True),
    Parameter("S_b", 1.8, None, constant=True),
    # Rate of appearance
    Parameter("k_max", 0.0558, U.per_min, constant=True),
    Parameter("k_min", 0.0080, U.per_min, constant=True),
    Parameter("k_abs", 0.057, U.per_min, constant=True),
    Parameter("k_gri", 0.0558, U.per_min, constant=True),
    Parameter("f", 0.90, U.dimensionless, constant=True),
    # Parameter('a', 0.00013, U.per_mg, constant=True),
    Parameter("b", 0.82, U.dimensionless, constant=True),
    # Parameter('c', 0.00236, U.per_mg, constant=True),
    Parameter("d", 0.010, U.dimensionless, constant=True),
    # Endogenous production
    Parameter("k_p1", 2.70, U.mg_per_kgmin, constant=True),
    Parameter("k_p2", 0.0021, U.per_min, constant=True),
    Parameter("k_p3", 0.009, U.mgl_per_kgminpmol, constant=True),
    Parameter("k_p4", 0.0618, U.mg_per_minpmol, constant=True),
    Parameter("k_i", 0.0079, U.per_min, constant=True),
    # Utilization
    Parameter(
        "U_ii",
        1,
        U.mg_per_kgmin,
        constant=True,
        name="insulin independent glucose utilization",
    ),  # F_cns
    Parameter("V_m0", 2.50, U.mg_per_kgmin, constant=True),
    Parameter("V_mX", 0.047, U.mgl_per_kgminpmol, constant=True),
    Parameter("K_m0", 225.59, U.mg_per_kg, constant=True),
    Parameter("V_f0", 2.5, U.mg_per_kgmin, constant=True),
    Parameter("V_fX", 0.047, U.mgl_per_kgminpmol, constant=True),
    Parameter("K_f0", 225.59, U.mg_per_kg, constant=True),
    Parameter("p_2U", 0.0331, U.per_min, constant=True),
    Parameter("part", 0.20, None, constant=True),
    # Secretion
    Parameter("K", 2.30, U.pmolmg_per_kgdl, constant=True),
    Parameter("alpha", 0.050, U.per_min, constant=True),
    Parameter("beta", 0.11, U.pmolmg_per_kgmindl, constant=True),
    Parameter("gamma", 0.5, U.per_min, constant=True),
    # renal excretion
    Parameter("k_e1", 0.0005, U.per_min, constant=True),
    Parameter("k_e2", 339, U.mg_per_kg, constant=True),
]

# ---------------------------------------------------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------------------------------------------------
_m.rate_rules = [
    # rate rules d/dt
    RateRule("Gp", "EGP +Ra -U_ii -E -k_1*Gp +k_2*Gt", U.mg_per_kgmin),
    RateRule("Gt", "-U_id + k_1*Gp -k_2*Gt", U.mg_per_kgmin),
    RateRule("Il", "-(m_1+m_3)*Il + m_2*Ip + S", U.pmol_per_kg),
    RateRule("Ip", "-(m_2+m_4)*Ip + m_1*Il", U.pmol_per_kg),
    RateRule("Qsto1", "-k_gri*Qsto1", None),
    RateRule("Qsto2", "(-k_empt*Qsto2)+k_gri*Qsto1", None),
    RateRule("Qgut", "(-k_abs*Qgut)+k_empt*Qsto2", None),
    RateRule("I1", "-k_i*(I1-I)", None),
    RateRule("Id", "-k_i*(Id-I1)", None),
    RateRule("INS", "(-p_2U*INS)+p_2U*(I-I_b)", None),
    RateRule("Ipo", "(-gamma*Ipo)+S_po", None),
    RateRule("Y", "-alpha*(Y-beta*(G-G_b))", None),
]

_m.rules = [
    AssignmentRule("aa", "5/2/(1-b)/D", None),
    AssignmentRule("cc", "5/2/d/D", None),
    AssignmentRule(
        "EGP",
        "k_p1-k_p2*Gp-k_p3*Id-k_p4*Ipo",
        U.mg_per_kgmin,
        name="EGP endogenous glucose production",
    ),
    AssignmentRule("V_mmax", "(1-part)*(V_m0+V_mX*INS)", None),
    AssignmentRule("V_fmax", "part*(V_f0+V_fX*INS)", None),
    AssignmentRule("E", "0", U.mg_per_kgmin, "renal excretion"),
    AssignmentRule("S", "gamma*Ipo", U.pmol_per_kgmin, name="S insulin secretion"),
    AssignmentRule("I", "Ip/V_I", U.pmol_per_l, name="I plasma insulin"),
    AssignmentRule("G", "Gp/V_G", U.mg_per_dl, name="G plasma Glucose"),
    AssignmentRule(
        "HE", "-m_5*S + m_6", U.dimensionless, name="HE hepatic extraction insulin"
    ),
    AssignmentRule("m_3", "HE*m_1/(1-HE)", U.per_min),
    AssignmentRule("Q_sto", "Qsto1+Qsto2", None),
    AssignmentRule(
        "Ra",
        "1.32 dimensionless*f*k_abs*Qgut/BW",
        U.mg_per_kgmin,
        name="Ra glucose rate of appearance",
    ),
    # % Ra', f*k_abs*Qgut/BW
    AssignmentRule(
        "k_empt",
        "k_min+(k_max-k_min)/2*(tanh(aa*(Q_sto-b*D))-tanh(cc*(Q_sto-d*D))+2)",
        None,
    ),
    AssignmentRule("U_idm", "V_mmax*Gt/(K_m0+Gt)", U.mg_per_kgmin),
    AssignmentRule("U_idf", "V_fmax*Gt/(K_f0+Gt)", U.mg_per_kgmin),
    AssignmentRule(
        "U_id",
        "U_idm+U_idf",
        U.mg_per_kgmin,
        name="insulin dependent glucose utilization",
    ),
    AssignmentRule("U", "U_ii+U_id", U.mg_per_kgmin, name="U glucose uptake"),
    AssignmentRule("S_po", "Y+K*(EGP+Ra-E-U_ii-k_1*Gp+k_2*Gt)/V_G+S_b", None),
]

dallaman_model = _m
