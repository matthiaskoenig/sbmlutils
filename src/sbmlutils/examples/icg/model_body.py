"""PKPD model for whole-body icg metabolism."""
import os

import numpy as np

from sbmlutils.cytoscape import visualize_sbml
from sbmlutils.examples.icg import annotations, templates
from sbmlutils.factory import *
from sbmlutils.log import get_logger
from sbmlutils.metadata import *


logger = get_logger(__name__)


# -------------------------------------------------------------------------------------
# Whole body model
# -------------------------------------------------------------------------------------
class U(Units):
    """UnitDefinitions."""

    mmole = UnitDefinition("mmole", "mmole")
    min = UnitDefinition("min", "min")
    kg = UnitDefinition("kg", "kg")
    m = UnitDefinition("m", "meter")
    m2 = UnitDefinition("m2", "meter^2")
    mM = UnitDefinition("mM", "mmole/liter")
    mmole_per_min = UnitDefinition("mmole_per_min", "mmole/min")
    mmole_per_min_l = UnitDefinition("mmole_per_min_l", "mmole/min/l")
    l_per_min = UnitDefinition("l_per_min", "l/min")
    per_min = UnitDefinition("per_min", "1/min")
    s = UnitDefinition("s", "second")
    mg = UnitDefinition("mg", "mg")
    ml = UnitDefinition("ml", "ml")
    hr = UnitDefinition("hr", "hr")
    per_hr = UnitDefinition("per_hr", "1/hr")
    cm = UnitDefinition("cm", "cm")
    mg_per_l = UnitDefinition("mg_per_l", "mg/l")
    mg_per_g = UnitDefinition("mg_per_g", "mg/g")
    mg_per_hr = UnitDefinition("mg_per_hr", "mg/hr")
    l_per_hr = UnitDefinition("l_per_hr", "l/hr")
    l_per_kg = UnitDefinition("l_per_kg", "l/kg")
    l_per_ml = UnitDefinition("l_per_ml", "l/ml")
    g_per_mole = UnitDefinition("g_per_mole", "g/mole")
    m2_per_kg = UnitDefinition("m2_per_kg", "meter^2/kg")
    mg_per_min = UnitDefinition("mg_per_min", "mg/min")
    mmole_per_hr = UnitDefinition("mmole_per_hr", "mmole/hr")
    mmole_per_min_kg = UnitDefinition("mmole_per_min_kg", "mmole/min/kg")
    mmole_per_hr_ml = UnitDefinition("mmole_per_hr_ml", "mmole/hr/ml")
    ml_per_s = UnitDefinition("ml_per_s", "ml/s")
    ml_per_s_kg = UnitDefinition("ml_per_s_kg", "ml/s/kg")
    ml_per_l = UnitDefinition("ml_per_l", "ml/l")
    mul_per_g = UnitDefinition("mul_per_g", "microliter/g")
    mul_per_min_mg = UnitDefinition("mul_per_min_mg", "microliter/min/mg")
    min_per_hr = UnitDefinition("min_per_hr", "min/hr")
    s_per_min = UnitDefinition("s_per_min", "s/min")
    s_per_hr = UnitDefinition("s_per_hr", "s/hr")


_m = Model(
    "icg_body",
    name="whole-body PBPK model of ICG",
    notes="""
    # Whole-body PBPK model of ICG

    ## Description
    Model for whole-body distribution and elimination of indocyanine green
    encoded in <a href="http://sbml.org">SBML</a> format.

    **Assumptions:**

    - icg is only metabolized in the liver

    """
    + templates.terms_of_use,
    creators=templates.creators,
    units=U,
    model_units=ModelUnits(
        time=U.min,
        extent=U.mmole,
        substance=U.mmole,
        length=U.m,
        area=U.m2,
        volume=U.liter,
    ),
    annotations=[
        (BQB.IS, "taxonomy/9606"),  # Homo sapiens
        (BQB.IS_DESCRIBED_BY, "https://doi.org/10.1101/2021.06.15.448411"),  # bioRxiv
    ],
)

SUBSTANCES_BODY = {
    "icg": {
        "name": "icg",
        "unit": U.mmole,
        # initial concentration
        "cinit": 0.0,  # [mmole/l]
        # Molecular weight
        "Mr": 774.96493,  # [g/mole]
        # doses [mg]
        "IVDOSE": 0,  # flag to add injection & infusion kinetics to the model
        "ftissue": 0.0,  # [litre_per_min] distribution in tissues,
        "annotations": annotations.species["icg"],
    },
}

# -----------------------------------------------------------------------------
# Submodels
# -----------------------------------------------------------------------------
COMPARTMENTS_BODY = {
    "bi": "bile",
    "re": "rest",
    "gi": "gastrointestinal tract",
    "li": "liver",
    "lu": "lung",
    "ve": "venous plasma",
    "ar": "arterial plasma",
    "po": "portal vein",
    "hv": "hepatic vein",
}

SUBMODEL_SID_DICT = {  # tissue to submodel mapping
    "li": "LI",  # liver
}

liver_id = "icg_liver"
_m.external_model_definitions = [
    ExternalModelDefinition(
        sid="liver",
        source=f"{liver_id}.xml",
        modelRef=liver_id,
        name="liver model definition",
    ),
]

_m.submodels = [
    Submodel(
        sid=SUBMODEL_SID_DICT["li"],
        modelRef="liver",
        name="liver submodel",
    ),
]

for emd in _m.external_model_definitions:
    logger.info(f"{emd} ({os.path.abspath(emd.source)})")


# -------------------------------------------------------------------------------------------------
# Compartments
# -------------------------------------------------------------------------------------------------
_m.compartments = [
    Compartment(
        "Vbi",
        metaId="meta_Vbi",
        value=1,
        unit=U.liter,
        constant=False,
        name="bile",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["bi"],
    ),
    Compartment(
        "Vre",
        metaId="meta_Vre",
        value=1,
        unit=U.liter,
        constant=False,
        name="rest of body",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["re"],
    ),
    Compartment(
        "Vgi",
        metaId="meta_Vgu",
        value=1,
        unit=U.liter,
        constant=False,
        name="gastrointestinal tract",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["gi"],
    ),
    Compartment(
        "Vli",
        metaId="meta_Vli",
        value=1,
        unit=U.liter,
        constant=False,
        name="liver",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["li"],
    ),
    Compartment(
        "Vlu",
        metaId="meta_Vlu",
        value=1,
        unit=U.liter,
        constant=False,
        name="lung",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["lu"],
    ),
    Compartment(
        "Vve",
        metaId="meta_Vve",
        value=1,
        unit=U.liter,
        constant=False,
        name="venous plasma",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["ve"],
    ),
    Compartment(
        "Var",
        metaId="meta_Var",
        value=1,
        unit=U.liter,
        constant=False,
        name="arterial plasma",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["ar"],
    ),
    Compartment(
        "Vpo",
        metaId="meta_Vpo",
        value=1,
        unit=U.liter,
        constant=False,
        name="portal plasma",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["po"],
    ),
    Compartment(
        "Vhv",
        metaId="meta_Vhv",
        value=1,
        unit=U.liter,
        constant=False,
        name="hepatic venous plasma",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["hv"],
    ),
    Compartment(
        "Vfeces",
        metaId="meta_Vfeces",
        value=1,
        unit=U.liter,
        constant=True,
        name="feces",
        sboTerm=SBO.PHYSICAL_COMPARTMENT,
        annotations=annotations.compartments["feces"],
    ),
]

# create plasma and tissue compartments (for correct blood volume)
for cid in COMPARTMENTS_BODY.keys():
    if cid not in ["ar", "ve", "po", "hv", "bi"]:
        _m.compartments.extend(
            [
                Compartment(
                    f"V{cid}_tissue",
                    value=1,
                    unit=U.liter,
                    constant=False,
                    name=f"{cid} tissue",
                    metaId=f"meta_V{cid}_tissue",
                    port=True,
                    sboTerm=SBO.PHYSICAL_COMPARTMENT,
                    annotations=annotations.compartments["parenchyma"]
                    + [
                        (BQB.IS_PART_OF, aid[1])
                        for aid in annotations.compartments[cid]
                    ],
                ),
                Compartment(
                    f"V{cid}_plasma",
                    value=1,
                    unit=U.liter,
                    constant=False,
                    name=f"{cid} plasma",
                    metaId=f"meta_V{cid}_plasma",
                    port=True,
                    sboTerm=SBO.PHYSICAL_COMPARTMENT,
                    annotations=annotations.compartments["plasma"]
                    + [
                        (BQB.IS_PART_OF, aid[1])
                        for aid in annotations.compartments[cid]
                    ],
                ),
            ]
        )

# replace volumes of submodels
_m.replaced_elements = [
    # liver
    ReplacedElement(
        sid="Vli_tissue_RE",
        metaId="Vli_tissue_RE",
        elementRef="Vli_tissue",
        submodelRef=SUBMODEL_SID_DICT["li"],
        portRef=f"Vli{PORT_SUFFIX}",
    ),
    ReplacedElement(
        sid="Vli_plasma_RE",
        metaId="Vli_plasma_RE",
        elementRef="Vli_plasma",
        submodelRef=SUBMODEL_SID_DICT["li"],
        portRef=f"Vext{PORT_SUFFIX}",
    ),
    # bile
    ReplacedElement(
        sid="Vbi_RE",
        metaId="Vbi_RE",
        elementRef="Vbi",
        submodelRef=SUBMODEL_SID_DICT["li"],
        portRef=f"Vbi{PORT_SUFFIX}",
    ),
    # feces
    ReplacedElement(
        sid="Vfeces_RE",
        metaId="Vfeces_RE",
        elementRef="Vfeces",
        submodelRef=SUBMODEL_SID_DICT["li"],
        portRef=f"Vfeces{PORT_SUFFIX}",
    ),
]

# -------------------------------------------------------------------------------------
# Species
# -------------------------------------------------------------------------------------
_m.species = []
for sid, sdict in SUBSTANCES_BODY.items():
    # plasma species
    for cid, cname in COMPARTMENTS_BODY.items():
        if cid == "bi":
            continue
        if cid in ["ve", "ar", "po", "hv"]:
            sid_ex = f"C{cid}_{sid}"
            cid_ex = f"V{cid}"
        else:
            # plasma compartment
            sid_ex = f"C{cid}_plasma_{sid}"
            cid_ex = f"V{cid}_plasma"

        _m.species.append(
            Species(
                sid_ex,
                metaId=f"meta_{sid_ex}",
                initialConcentration=sdict["cinit"],  # type: ignore
                compartment=cid_ex,
                substanceUnit=sdict["unit"],  # type: ignore
                name=f"{sdict['name']} ({cname})",
                hasOnlySubstanceUnits=False,
                port=True,
                annotations=sdict["annotations"],  # type: ignore
                sboTerm=SBO.SIMPLE_CHEMICAL,
            )
        )

    if "ftissue" in sdict and not np.isclose(sdict["ftissue"], 0.0):
        # tissue species
        for cid, cname in COMPARTMENTS_BODY.items():
            if cid not in ["ve", "ar", "po", "hv", "li", "bi"]:
                sid_ex = f"C{cid}_{sid}"
                cid_ex = f"V{cid}_tissue"

                _m.species.extend(
                    [
                        Species(
                            sid_ex,
                            metaId=f"meta_{sid_ex}",
                            initialConcentration=sdict["cinit"],  # type: ignore
                            compartment=cid_ex,
                            substanceUnit=sdict["unit"],  # type: ignore
                            name=f"{sdict['name']} ({cname})",
                            hasOnlySubstanceUnits=False,
                            port=True,
                            annotations=sdict["annotations"],  # type: ignore
                            sboTerm=SBO.SIMPLE_CHEMICAL,
                        )
                    ]
                )

    if sid in ["icg"]:
        _m.species.append(
            Species(
                f"Afeces_{sid}",
                metaId=f"meta_Afeces_{sid}",
                initialConcentration=0,
                compartment="Vfeces",
                substanceUnit=sdict["unit"],  # type: ignore
                name=f"{sdict['name']} (feces)",
                hasOnlySubstanceUnits=True,
                annotations=sdict["annotations"],  # type: ignore
                sboTerm=SBO.SIMPLE_CHEMICAL,
            )
        )

# replace species
replaced_species = {
    "li": ["icg"],  # ['icg', 'bil'],
}
# plasma to external species
for tkey, skey_list in replaced_species.items():
    for skey in skey_list:
        _m.replaced_elements.extend(
            [
                ReplacedElement(
                    sid=f"C{tkey}_plasma_{skey}_RE",
                    metaId=f"C{tkey}_plasma_{skey}_RE",
                    elementRef=f"C{tkey}_plasma_{skey}",
                    submodelRef=SUBMODEL_SID_DICT[tkey],
                    portRef=f"{skey}_ext{PORT_SUFFIX}",
                )
            ]
        )

# replace ICG in feces
_m.replaced_elements.append(
    ReplacedElement(
        sid="Afeces_icg_RE",
        metaId="Afeces_icg_RE",
        elementRef="Afeces_icg",
        submodelRef=SUBMODEL_SID_DICT["li"],
        portRef=f"icg_feces{PORT_SUFFIX}",
    )
)

# -------------------------------------------------------------------------------------------------
# Parameters
# -------------------------------------------------------------------------------------------------
_m.parameters = [
    # --- conversion factors ---
    Parameter(
        "conversion_ml_per_l",
        1000,
        U.ml_per_l,
        constant=True,
        name="volume conversion factor",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
    ),
    Parameter(
        "conversion_l_per_ml",
        0.001,
        U.l_per_ml,
        constant=True,
        name="volume conversion factor",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
    ),
    # --- whole body data ---
    Parameter(
        "BW",
        75,
        U.kg,
        constant=True,
        name="body weight [kg]",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS, "efo/0004338"),
            (BQB.IS, "ncit/C25208"),
            (BQB.IS, "cmo/CMO:0000012"),
        ],
    ),
    Parameter(
        "HEIGHT",
        170,
        U.cm,
        constant=True,
        name="height [cm]",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS, "ncit/C25347"),
            (BQB.IS, "efo/0004339"),
        ],
    ),
    Parameter(
        "BSA",
        0,
        U.m2,
        constant=False,
        name="body surface area [m^2]",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[(BQB.IS, "ncit/C25157"), (BQB.IS, "omit/0003188")],
        notes="""

        """,
    ),
    Parameter(
        "COBW",
        75 / 60,
        U.ml_per_s_kg,
        constant=True,
        name="cardiac output per bodyweight [ml/s/kg]",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS, "ncit/C119246"),
            (BQB.IS, "omit/0003637"),
        ],
        notes="""Simone1997 75 [50-100] ml/min/kg""",
    ),
    Parameter(
        "CO",
        80 / 60 * 75,
        U.ml_per_s,
        constant=False,
        name="cardiac output [ml/s]",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS, "ncit/C119246"),
            (BQB.IS, "omit/0003637"),
        ],
        notes="""BW*COBW (100 ml/s)""",
    ),
    Parameter(
        "QC",
        80 / 60 * 75 / 1000 * 60,
        U.l_per_min,
        constant=False,
        name="cardiac output [L/min]",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS, "ncit/C119246"),
            (BQB.IS, "omit/0003637"),
        ],
        notes="""
        CO/1000 ml/l * 60 s/min (6 l/min)
        IRCP2001 reference values Cardiac output: 6.5 l/min (male); 5.9 l/min (female)
        Cardiac output at lower end => 3.75 l/min
        """,
    ),
    Parameter(
        "Fblood",
        0.02,
        U.dimensionless,
        constant=False,
        name="blood fraction of organ volume",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        notes="""
        A certain volume of an organ is occupied by large vessels (in the low
        percent range). This parameter describes this fraction.
        """,
    ),
    Parameter(
        "HCT",
        0.51,
        U.dimensionless,
        constant=True,
        metaId="meta_HCT",
        name="hematocrit",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS, "ncit/C64796"),
            (BQB.IS, "omit/0007571"),
            (BQB.IS, "efo/0004348"),
        ],
    ),
    # --- fractional tissue volumes ---
    Parameter(
        "FVgi",
        0.0297,
        U.l_per_kg,
        constant=True,
        name="fractional tissue volume gastrointestinal tract",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        notes="""FVgi = FVgu + FVpa + FVsp = 0.0171 + 0.01 + 0.0026 = 0.0297""",
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["gi"]
        ],
    ),
    Parameter(
        "FVbi",
        0.00071,
        U.l_per_kg,
        constant=True,
        name="fractional tissue volume bile",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["bi"]
        ],
    ),
    Parameter(
        "FVli",
        0.0210,
        U.l_per_kg,
        constant=True,
        name="fractional tissue volume liver",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        notes="""
        1.7-1.8 kg (male); 1.5 kg (female); 75kg; 1.7/75 = 0.0227
        """,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["li"]
        ],
    ),
    Parameter(
        "FVlu",
        0.0076,
        U.l_per_kg,
        constant=True,
        name="fractional tissue volume lung",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["lu"]
        ],
    ),
    # 20% / 64%
    # FVve + FVar = 0.0771
    # 64/84; FVve = 0.0587
    # 20/84; Far  = 0.0184
    Parameter(
        "FVve",
        0.0587,
        U.l_per_kg,
        constant=True,
        name="fractional tissue volume venous",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["ve"]
        ],
    ),
    Parameter(
        "FVar",
        0.0184,
        U.l_per_kg,
        constant=True,
        name="fractional tissue volume arterial",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["ar"]
        ],
    ),
    Parameter(
        "FVpo",
        0.001,
        U.l_per_kg,
        constant=True,
        name="fractional tissue volume portal",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["po"]
        ],
    ),
    Parameter(
        "FVhv",
        0.001,
        U.l_per_kg,
        constant=True,
        name="fractional tissue volume hepatic venous",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["hv"]
        ],
    ),
    Parameter(
        "FVre",
        0,
        U.l_per_kg,
        constant=False,
        name="fractional tissue volume rest of body",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["re"]
        ],
        notes="""
        Fraction is calculated based on other volume fractions.
        """,
    ),
    # fractional tissue blood flows
    # FQgi = FQgu + FQpa + FQsp = 0.146 + 0.017 + 0.017 = 0.18
    # 20 % arteriell; 80 % portal vein (gi) => 0.172
    # FQgi < FQh
    # IRCP2001 reference value arterial: 0.065 (male/female);
    # FQgi = FQpo = FQh - FQha = 0.255 - 0.065 = 0.190
    Parameter(
        "FQgi",
        0.190,
        U.dimensionless,
        constant=True,
        name="gastrointestinal tract fractional tissue blood flow",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["gi"]
        ],
    ),
    # IRCP2001 reference value total liver: 0.255 (male); 0.270 (female)
    Parameter(
        "FQh",
        0.255,
        U.dimensionless,
        constant=True,
        name="hepatic (venous side) fractional tissue blood flow",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["hv"]
        ],
    ),
    Parameter(
        "FQlu",
        1,
        U.dimensionless,
        constant=True,
        name="lung fractional tissue blood flow",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["lu"]
        ],
    ),
    Parameter(
        "FQre",
        0,
        U.dimensionless,
        constant=False,
        name="rest of body fractional tissue blood flow",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, item[1]) for item in annotations.compartments["re"]
        ],
        notes="""
        Calculated based on other tissue blood flow and flow conservation laws.
        """,
    ),
    # FIXME: we want to sample hepatic blood flow/bodyweight Qhbw
    # Qh = CO * FQh * f_bloodflow
    # Qhbw = Qh/BW = CO * FQh * f_bloodflow/BW
    # f_bloodflow = Qhbw*BW/CO/FQh
    # Qh = QC*FQh*f_bloodflow
    # QC = CO/1000 ml_per_l * 60 s_per_min' # 'l_per_min'
    # CO = BW*COBW*f_cardiac_output'  # 'ml_per_s'
    # =>
    # Qh = BW*COBW*f_cardiac_output * 60/1000 * FQh * f_bloodflow
    # Qhbw = COBW*f_cardiac_output * 60/1000 * FQh * f_bloodflow
    # => f_bloodflow = Qhbw/(COBW*f_cardiac_output * 60/1000 * FQh)
    # => f_bloodflow = Qhbw/(COBW * 60/1000 * FQh); with COBW = 50/60 [ml_per_s_kg];
    #     FQh = 0.255 [-];
    # --- changes for cirrhotic liver ---
    Parameter(
        "f_cirrhosis",
        0,
        U.dimensionless,
        constant=True,
        name="severity of cirrhosis [0, 0.95]",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS, "ncit/C2951"),  # Cirrhosis
            (BQB.IS, "efo/0001422"),  # cirrhosis of liver
        ],
    ),
    Parameter(
        "f_shunts",
        0,
        U.dimensionless,
        constant=True,
        name="fraction of portal venous blood shunted by the liver",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS, "hp/HP:0002629"),  # Gastrointestinal arteriovenous malformation
        ],
    ),
    Parameter(
        "f_tissue_loss",
        0,
        U.dimensionless,
        constant=True,
        name="fraction of lost parenchymal liver volume",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
    ),
    # --- changes for blood flow experiments ---
    # f_bloodflow must not be >4.651, otherwise Qh > Qlu + Qre resulting in negative
    # flux values
    Parameter(
        "f_bloodflow",
        1,
        U.dimensionless,
        constant=True,
        name="fractional change of hepatic blood flow",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
    ),
    Parameter(
        "f_cardiac_output",
        1,
        U.dimensionless,
        constant=True,
        name="fractional change of cardiac output",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
    ),
    Parameter(
        "f_exercise",
        1,
        U.dimensionless,
        constant=True,
        name="fractional blood flow change due to exercise",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
    ),
    # --- changes for hepatectomy experiments ---
    Parameter(
        "resection_rate",
        0,
        U.dimensionless,
        constant=True,
        name="resection rate",
        sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
        annotations=[
            (BQB.IS_VERSION_OF, "ncit/C158758"),  # Resection
        ],
    ),
]

# species specific parameters
for sid, sdict in SUBSTANCES_BODY.items():
    _m.parameters.extend(
        [
            # molecular weights
            Parameter(
                f"Mr_{sid}",
                sdict["Mr"],  # type: ignore
                U.g_per_mole,
                constant=True,
                name=f"Molecular weight {sid} [g/mole]",
                sboTerm=SBO.MOLECULAR_MASS,
                annotations=[
                    (BQB.IS_VERSION_OF, "opb/OPB_01146"),  # Molecular weight
                    (BQB.HAS_PART, sdict["annotations"][0][1]),  # type: ignore
                ],
            ),
        ]
    )

    if "ftissue" in sdict and not np.isclose(sdict["ftissue"], 0.0):
        _m.parameters.extend(
            [
                # tissue distribution
                Parameter(
                    f"ftissue_{sid}",
                    sdict["ftissue"],  # type: ignore
                    U.l_per_min,
                    constant=True,
                    name=f"tissue distribution {sid}",
                    sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
                ),
            ]
        )

    if "IVDOSE" in sdict:
        _m.parameters.extend(
            [
                # dosing
                Parameter(
                    f"IVDOSE_{sid}",
                    sdict["IVDOSE"],  # type: ignore
                    U.mg,
                    constant=False,
                    name=f"IV bolus dose {sid} [mg]",
                    sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
                    annotations=[(BQB.IS, "ncit/C38274")],
                ),
                # iv kinetics after application
                Parameter(
                    f"ti_{sid}",
                    5,
                    U.s,
                    constant=True,
                    name=f"injection time {sid} [s]",
                    sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
                    annotations=[(BQB.IS, "ncit/C69282")],
                ),
                Parameter(
                    f"Ki_{sid}",
                    0.02,
                    U.per_min,
                    constant=False,
                    name=f"Ki [1/min] injection {sid}",
                    sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
                ),
                # continuous infusion
                Parameter(
                    f"Ri_{sid}",
                    0,
                    U.mg_per_min,
                    constant=True,
                    name=f"Ri [mg/min] rate of infusion {sid}",
                    sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
                    annotations=[(BQB.IS, "ncit/C94916")],
                ),
                Parameter(
                    f"cum_dose_{sid}",
                    0,
                    U.mg,
                    constant=False,
                    name=f"Cumulative dose due to infusion {sid}",
                    sboTerm=SBO.QUANTITATIVE_SYSTEMS_DESCRIPTION_PARAMETER,
                    annotations=[
                        (BQB.IS, "ncit/C94394"),
                    ]
                    + annotations.species["icg"],
                ),
            ]
        )

# -------------------------------------------------------------------------------------------------
# AssignmentRules
# -------------------------------------------------------------------------------------------------
_m.rules = [
    AssignmentRule(
        "FVre",
        "1.0 l_per_kg - (FVbi + FVgi + FVli + FVlu + FVve + FVar + FVpo + FVhv)",
        U.l_per_kg,
        name="rest body volume",
        notes="""
        Remaining volume based on fractional organ volume is used for the rest
        compartment.
        """,
    ),
    AssignmentRule(
        "FQre",
        "1.0 dimensionless - Qh/Qlu",
        U.dimensionless,
        name="rest body perfusion",
        notes="""
        Rest body perfusion .must be calculate based on flux conservation laws.
        ```
        Qlu = Qre + Qh
        Qre = Qlu - Qh
        FQre = (Qlu - Qh) / Qlu = 1 - Qh/Qlu
        ```
        """,
    ),
    AssignmentRule(
        "BSA",
        "0.024265 m2 * power(BW/1 kg, 0.5378) * power(HEIGHT/1 cm, 0.3964)",
        U.m2,
        name="body surface area (BSA)",
        notes="""
        Calculated with Haycock1978 formula.
        """,
    ),
    AssignmentRule(
        "CO",
        "BW*COBW*f_cardiac_output",
        U.ml_per_s,
        name="cardiac output",
    ),
    AssignmentRule(
        "QC", "CO/1000 ml_per_l * 60 s_per_min", U.l_per_min, name="cardiac blood flow"
    ),
    # volumes
    AssignmentRule("Vbi", "BW*FVbi", U.liter, name="volume bile"),
    AssignmentRule("Vgi", "BW*FVgi", U.liter, name="volume gastrointestinal tract"),
    AssignmentRule(
        "Vli",
        "BW*FVli*(1 dimensionless - resection_rate)",
        U.liter,
        name="volume liver",
    ),
    AssignmentRule("Vlu", "BW*FVlu", U.liter, name="volume lung"),
    AssignmentRule("Vre", "BW*FVre", U.liter, name="volume rest body"),
    # venous and arterial plasma volume (corrected for tissue blood volumes)
    AssignmentRule(
        "Vve",
        "(1 dimensionless - HCT) * (BW*FVve - FVve/(FVar+FVve+FVpo+FVhv) * BW * "
        "Fblood * (1 l_per_kg - (FVar+FVve+FVpo+FVhv)))",
        U.liter,
        name="volume venous plasma",
    ),
    AssignmentRule(
        "Var",
        "(1 dimensionless - HCT) * (BW*FVar - FVar/(FVar+FVve+FVpo+FVhv) * BW * "
        "Fblood * (1 l_per_kg - (FVar+FVve+FVpo+FVhv)))",
        U.liter,
        name="volume arterial plasma",
    ),
    AssignmentRule(
        "Vpo",
        "(1 dimensionless - HCT) * (BW*FVpo - FVpo/(FVar+FVve+FVpo+FVhv) * BW * "
        "Fblood * (1 l_per_kg - (FVar+FVve+FVpo+FVhv)))",
        U.liter,
        name="volume hepatic portal plasma",
    ),
    AssignmentRule(
        "Vhv",
        "(1 dimensionless - HCT) * (BW*FVhv - FVhv/(FVar+FVve+FVpo+FVhv) * "
        "BW * Fblood * (1 l_per_kg - (FVar+FVve+FVpo+FVhv)))",
        U.liter,
        name="volume hepatic venous plasma",
    ),
    # blood flows
    AssignmentRule("Qlu", "QC*FQlu", U.l_per_min, name="blood flow lung"),
    AssignmentRule("Qre", "QC*FQre", U.l_per_min, name="blood flow rest of body"),
    AssignmentRule(
        "Qh",
        "QC*FQh*f_bloodflow*f_exercise",
        U.l_per_min,
        name="blood flow hepatic (venous side)",
    ),
    AssignmentRule(
        "Qgi",
        "QC*FQgi*f_bloodflow",
        U.l_per_min,
        name="blood flow gastrointestinal tract",
    ),
    AssignmentRule("Qpo", "Qgi", U.l_per_min, name="blood flow portal vein"),
    AssignmentRule("Qha", "Qh - Qpo", U.l_per_min, name="blood flow hepatic artery"),
]

# Volumes for explicit tissue models
for cid, cname in COMPARTMENTS_BODY.items():
    if cid not in ["ve", "ar", "po", "hv", "bi"]:
        _m.rules.append(
            # plasma volume associated with tissue
            AssignmentRule(
                f"V{cid}_plasma",
                value=f"V{cid} * Fblood * (1 dimensionless - HCT)",
                unit=U.liter,
                name=f"plasma volume of {cname}",
            ),
        )

        if cid == "li":
            _m.rules.append(
                # Cirrhosis: Adjustment of fractional liver tissue volume
                AssignmentRule(
                    f"V{cid}_tissue",
                    value=f"V{cid}*(1 dimensionless - f_tissue_loss) * "
                    f"(1 dimensionless - Fblood)",
                    unit=U.liter,
                    name=f"tissue volume of {cname}",
                ),
            )
        else:
            _m.rules.append(
                AssignmentRule(
                    f"V{cid}_tissue",
                    value=f"V{cid}*(1 dimensionless - Fblood)",
                    unit=U.liter,
                    name=f"tissue volume of {cname}",
                ),
            )

for sid, sdict in SUBSTANCES_BODY.items():
    sname = sdict["name"]

    if "IVDOSE" in sdict:
        # injection
        _m.rules.extend(
            [
                AssignmentRule(
                    f"Ki_{sid}",
                    f"0.693 dimensionless/ti_{sid} * 60 s_per_min",
                    U.per_min,
                    name="injection rate IV",
                ),
            ]
        )

    # ---------------------------------
    # X Amount [mg], C Concentration
    # ---------------------------------
    for cid, cname in COMPARTMENTS_BODY.items():
        if cid == "bi":
            continue

        if cid not in ["ve", "ar", "po", "hv"]:
            _m.rules.extend(
                [
                    AssignmentRule(
                        f"A{cid}_plasma_{sid}",
                        f"C{cid}_plasma_{sid}*V{cid}_plasma",
                        U.mmole,
                        name=f"{sname} concentration ({cname})",
                    ),
                    AssignmentRule(
                        f"X{cid}_plasma_{sid}",
                        f"A{cid}_plasma_{sid}*Mr_{sid}",
                        U.mg,
                        name=f"{sname} amount ({cname})",
                    ),
                    AssignmentRule(
                        f"M{cid}_plasma_{sid}",
                        f"A{cid}_plasma_{sid}/V{cid}_plasma*Mr_{sid}",
                        U.mg_per_l,
                        name=f"{sname} amount ({cname})",
                    ),
                ]
            )
        else:
            _m.rules.extend(
                [
                    AssignmentRule(
                        f"A{cid}_{sid}",
                        f"C{cid}_{sid}*V{cid}",
                        U.mmole,
                        name=f"{sname} concentration ({cname})",
                    ),
                    AssignmentRule(
                        f"X{cid}_{sid}",
                        f"A{cid}_{sid}*Mr_{sid}",
                        U.mg,
                        name="{sname} amount ({cname})",
                    ),
                    AssignmentRule(
                        f"M{cid}_{sid}",
                        f"A{cid}_{sid}/V{cid}*Mr_{sid}",
                        U.mg_per_l,
                        name=f"{sname} amount ({cname})",
                    ),
                ]
            )

_m.rules.extend(
    [
        # FIXME: divide by zero in model equation at time zero
        #  (handled by very small concentration offset)
        # FIXME: many issues with numerical tolerances
        AssignmentRule(
            "ER_icg",
            "(Car_icg + 1E-7 mM -(Chv_icg+1E-7mM))/(Car_icg + 1E-7 mM)",
            U.dimensionless,
            name="extraction ratio ICG",
        ),
        # Clearance calculated during steady state in continous infusion
        # Ri_icg [mg/min] / Cve_icg / Mr_icg [mmole/l]  -> [(g*l)/(min*mole)]  [ml/min]
        # FIXME: divide by zero
        AssignmentRule(
            "CLinfusion_icg",
            "Ri_icg/Mr_icg/(Cve_icg + 1E-12 mM)",
            U.l_per_min,
            # f'Ri_icg/Mr_icg/Cve_icg', U.litre_per_min,
            name="infusion clearance (steady state)",
        ),
    ]
)


# -------------------------------------------------------------------------------------
# Reactions
# -------------------------------------------------------------------------------------
_m.reactions = []

for sid, sdict in SUBSTANCES_BODY.items():
    sname = sdict["name"]

    # --------------------
    # tissue distribution
    # --------------------
    if "ftissue" in sdict and not np.isclose(sdict["ftissue"], 0.0):
        for cid in COMPARTMENTS_BODY.keys():
            if cid not in ["ve", "ar", "po", "hv", "li", "bi"]:
                _m.reactions.append(
                    Reaction(
                        sid=f"transport_{cid}_{sid}",
                        name=f"transport {sname}",
                        formula=(
                            f"ftissue_{sid} * (C{cid}_plasma_{sid} - C{cid}_{sid})",
                            U.mmole_per_min,
                        ),
                        equation=f"C{cid}_plasma_{sid} <-> C{cid}_{sid}",
                        compartment=f"V{cid}_tissue",
                        sboTerm=SBO.TRANSPORT_REACTION,
                    ),
                )

    if "IVDOSE" in sdict:
        _m.reactions.extend(
            [
                # --------------------
                # iv application
                # --------------------
                Reaction(
                    sid=f"iv_{sid}",
                    name=f"iv {sname}",
                    formula=(f"Ki_{sid}*IVDOSE_{sid}/Mr_{sid}", U.mmole_per_min),
                    equation=f"-> Cve_{sid}",
                    compartment="Vve",
                    sboTerm=SBO.TRANSPORT_REACTION,
                    annotations=[(BQB.IS, "ncit/C38276")],
                ),
            ]
        )

    # --------------------
    # blood flow model
    # --------------------
    for cid, cname in COMPARTMENTS_BODY.items():
        if cid in ["ve", "ar", "po", "hv"]:
            continue
        # --------------------
        # ve -> lung -> ar
        # --------------------
        if cid == "lu":
            rid_in = f"Flow_ve_{cid}_{sid}"
            name_in = f"inflow {cname} {sname}"

            rid_out = f"Flow_{cid}_ar_{sid}"
            name_out = f"outflow {cname} {sname}"

            # distribution in plasma volume
            _m.reactions.extend(
                [
                    Reaction(
                        sid=rid_in,
                        name=name_in,
                        formula=(f"Q{cid}*Cve_{sid}", U.mmole_per_min),
                        equation=f"Cve_{sid} -> C{cid}_plasma_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                    ),
                    Reaction(
                        sid=rid_out,
                        name=name_out,
                        formula=(f"Q{cid}*C{cid}_plasma_{sid}", U.mmole_per_min),
                        equation=f"C{cid}_plasma_{sid} -> Car_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                    ),
                ]
            )
        # ------------------------------------------
        # ar -> arorgan -> organ -> ve
        # ------------------------------------------
        if cid in ["re"]:
            rid_in1 = f"Flow_ar_ar{cid}_{sid}"
            rid_in2 = f"Flow_ar{cid}_{cid}_{sid}"
            name_in = f"inflow {cname} {sname}"
            rid_out = f"Flow_{cid}_ve_{sid}"
            name_out = f"outflow {cname} {sname}"

            # only distribution in plasma volume
            _m.reactions.extend(
                [
                    Reaction(
                        sid=rid_in1,
                        name=name_in,
                        formula=(f"Q{cid}*Car_{sid}", U.mmole_per_min),
                        equation=f"Car_{sid} -> C{cid}_plasma_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                        annotations=[(BQB.IS, "ncit/C16353")]
                        + [
                            (BQB.IS_PART_OF, aid[1])
                            for aid in annotations.compartments[cid]
                        ],
                    ),
                    Reaction(
                        sid=rid_out,
                        name=name_out,
                        formula=(f"Q{cid}*C{cid}_plasma_{sid}", U.mmole_per_min),
                        equation=f"C{cid}_plasma_{sid} -> Cve_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                        annotations=[(BQB.IS, "ncit/C16353")]
                        + [
                            (BQB.IS_PART_OF, aid[1])
                            for aid in annotations.compartments[cid]
                        ],
                    ),
                ]
            )
        # -----------------------------
        # ar -> arorgan -> organ -> po
        # -----------------------------
        if cid in ["gi"]:
            rid_in1 = f"Flow_ar_ar{cid}_{sid}"
            rid_in2 = f"Flow_ar{cid}_{cid}_{sid}"
            name_in = f"inflow {cname} {sname}"

            rid_out = f"Flow_{cid}_po_{sid}"
            name_out = f"outflow {cname} {sname}"

            _m.reactions.extend(
                [
                    # only distribution in plasma volume
                    Reaction(
                        sid=rid_in1,
                        name=name_in,
                        formula=(f"Q{cid}*Car_{sid}", U.mmole_per_min),
                        equation=f"Car_{sid} -> C{cid}_plasma_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                        annotations=[(BQB.IS, "ncit/C16353")]
                        + [
                            (BQB.IS_PART_OF, aid[1])
                            for aid in annotations.compartments[cid]
                        ],
                    ),
                    Reaction(
                        sid=rid_out,
                        name=name_out,
                        formula=(f"Q{cid}*C{cid}_plasma_{sid}", U.mmole_per_min),
                        equation=f"C{cid}_plasma_{sid} -> Cpo_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                        annotations=[(BQB.IS, "ncit/C16353")]
                        + [
                            (BQB.IS_PART_OF, aid[1])
                            for aid in annotations.compartments[cid]
                        ],
                    ),
                ]
            )
        # --------------------
        # ar -> arli -> li
        # po -> li
        # li -> hv -> ve
        # --------------------
        if cid == "li":
            _m.reactions.extend(
                [
                    Reaction(
                        sid=f"Flow_arli_li_{sid}",
                        name=f"arterial inflow liver {sname}",
                        formula=(
                            f"(1 dimensionless - f_shunts)*Qha*Car_{sid}",
                            U.mmole_per_min,
                        ),
                        equation=f"Car_{sid} -> Cli_plasma_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                    ),
                    # shunted arterial flow
                    Reaction(
                        sid=f"Flow_arli_hv_{sid}",
                        name="flow arterial shunts",
                        formula=(f"f_shunts*Qha*Car_{sid}", U.mmole_per_min),
                        equation=f"Car_{sid} -> Chv_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                    ),
                    # (unshunted) portal flow
                    Reaction(
                        sid=f"Flow_po_li_{sid}",
                        name=f"outflow po {sname}",
                        formula=(
                            f"(1 dimensionless - f_shunts)*Qpo*Cpo_{sid}",
                            U.mmole_per_min,
                        ),
                        equation=f"Cpo_{sid} -> Cli_plasma_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                    ),
                    # portal shunts
                    Reaction(
                        sid=f"Flow_po_hv_{sid}",
                        name="flow portal shunts",
                        formula=(f"f_shunts*Qpo*Cpo_{sid}", U.mmole_per_min),
                        equation=f"Cpo_{sid} -> Chv_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                    ),
                    Reaction(
                        sid=f"Flow_li_hv_{sid}",
                        name=f"outflow liver {sname}",
                        formula=(
                            f"(1 dimensionless - f_shunts)*(Qpo+Qha)*Cli_plasma_{sid}",
                            U.mmole_per_min,
                        ),
                        equation=f"Cli_plasma_{sid} -> Chv_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                    ),
                    Reaction(
                        sid=f"Flow_hv_ve_{sid}",
                        name=f"outflow hepatic vein {sname}",
                        formula=(f"Qh*Chv_{sid}", U.mmole_per_min),
                        equation=f"Chv_{sid} -> Cve_{sid}",
                        sboTerm=SBO.TRANSPORT_REACTION,
                    ),
                ]
            )

# --------------------------------------------------------------------------------------------------
# RateRules
# --------------------------------------------------------------------------------------------------
_m.rate_rules = []

for sid, sdict in SUBSTANCES_BODY.items():
    if "IVDOSE" in sdict:
        _m.rate_rules.extend(
            [
                # injection of dose
                RateRule(
                    f"IVDOSE_{sid}",
                    f"-iv_{sid}*Mr_{sid} + Ri_{sid}",
                    U.mg_per_min,
                    name="change of injected dose",
                    notes="""
                    The injected dose appears in the blood over time.
                    """,
                ),
                # cumulative infusion dose
                RateRule(
                    f"cum_dose_{sid}",
                    f"Ri_{sid}",
                    U.mg_per_min,
                    name="cumulative injected dose",
                ),
            ]
        )

model_body = _m

if __name__ == "__main__":
    from sbmlutils.examples.icg import MODEL_BASE_PATH

    results = create_model(
        model=model_body,
        filepath=MODEL_BASE_PATH / f"{model_body.sid}.xml",
    )
    visualize_sbml(results.sbml_path)
