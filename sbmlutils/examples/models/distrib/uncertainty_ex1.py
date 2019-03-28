# -*- coding=utf-8 -*-
"""
Distrib example.
"""

from sbmlutils.units import *
from sbmlutils.sbo import *
from sbmlutils.factory import *
from sbmlutils.modelcreator import templates

# -----------------------------------------------------------------------------
mid = 'uncertainty_ex1'
version = 1
creators = templates.creators
notes = Notes([
    """
    <h1>sbmlutils {}</h1>
    <h2>Description</h2>
    <p>Example creating distrib model with uncertainty elements.</p>
    """,
    templates.terms_of_use
])

# -----------------------------------------------------------------------------
# Units
# -----------------------------------------------------------------------------

model_units = ModelUnits(time=UNIT_h, extent=UNIT_KIND_MOLE, substance=UNIT_KIND_MOLE,
                         length=UNIT_m, area=UNIT_m2, volume=UNIT_KIND_LITRE)
units = [
    UNIT_h, UNIT_m, UNIT_m2,
]


# -----------------------------------------------------------------------------
# Units
# -----------------------------------------------------------------------------
parameters = [
    Parameter(sid="p1", value=1.0, unit=UNIT_KIND_MOLE, constant=True, uncertainties=[

    ])
]
