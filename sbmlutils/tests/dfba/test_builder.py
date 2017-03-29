from __future__ import print_function, absolute_import
import libsbml

from sbmlutils import factory as fac
from sbmlutils.dfba import builder

import matplotlib
matplotlib.use('Agg')


def create_fba_doc():
    sbmlns = libsbml.SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("fbc", 2)
    sbmlns.addPackageNamespace("comp", 1)

    doc = libsbml.SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    doc.setPackageRequired("fbc", False)
    model = doc.createModel()
    mplugin = model.getPlugin("fbc")
    mplugin.setStrict(True)

    objects = [
        fac.Compartment(sid='cell', value=1.0),
        fac.Species(sid='A', value=0, compartment="cell"),
        fac.Species(sid='B', value=0, compartment="cell"),
    ]
    fac.create_objects(model, objects)

    return doc


def test_create_exchange_reaction():
    doc = create_fba_doc()
    model = doc.getModel()

    builder.create_exchange_reaction(model, species_id="A")
    builder.create_exchange_reaction(model, species_id="B")

    assert model.getNumReactions() == 2
    ex_A = model.getReaction(builder.EXCHANGE_REACTION_PREFIX + "A")
    assert ex_A
    ex_B = model.getReaction(builder.EXCHANGE_REACTION_PREFIX + "B")
    assert ex_B

    comp_model = model.getPlugin("comp")
    ports = comp_model.getListOfPorts()
    assert ports is not None
    assert comp_model.getNumPorts() == 6
    assert comp_model.getPort(builder.EXCHANGE_REACTION_PREFIX + "A_port")
    assert comp_model.getPort(builder.EXCHANGE_REACTION_PREFIX + "B_port")
    assert comp_model.getPort(builder.LOWER_BOUND_PREFIX + builder.EXCHANGE_REACTION_PREFIX + "A_port")
    assert comp_model.getPort(builder.LOWER_BOUND_PREFIX + builder.EXCHANGE_REACTION_PREFIX + "B_port")
    assert comp_model.getPort(builder.UPPER_BOUND_PREFIX + builder.EXCHANGE_REACTION_PREFIX + "A_port")
    assert comp_model.getPort(builder.UPPER_BOUND_PREFIX + builder.EXCHANGE_REACTION_PREFIX + "B_port")

    fbc_ex_A = ex_A.getPlugin("fbc")
    assert fbc_ex_A
    fbc_ex_B = ex_B.getPlugin("fbc")
    assert fbc_ex_B


def test_create_directed_exchange_reaction():
    doc = create_fba_doc()
    model = doc.getModel()

    builder.create_exchange_reaction(model, species_id="A", exchange_type=builder.EXCHANGE_IMPORT)
    builder.create_exchange_reaction(model, species_id="B", exchange_type=builder.EXCHANGE_EXPORT)

    assert model.getNumReactions() == 2

    # import
    ex_A = model.getReaction(builder.EXCHANGE_REACTION_PREFIX + "A")
    assert ex_A
    fbc_ex_A = ex_A.getPlugin("fbc")
    assert fbc_ex_A
    pid_ub = fbc_ex_A.getUpperFluxBound()
    p_ub = model.getParameter(pid_ub)
    assert p_ub
    assert p_ub.value == builder.ZERO_BOUND
    pid_lb = fbc_ex_A.getLowerFluxBound()
    p_lb = model.getParameter(pid_lb)
    assert p_lb
    assert p_lb.value == builder.LOWER_BOUND_DEFAULT

    # export
    ex_B = model.getReaction(builder.EXCHANGE_REACTION_PREFIX + "B")
    assert ex_B
    fbc_ex_B = ex_B.getPlugin("fbc")
    assert fbc_ex_B
    pid_ub = fbc_ex_B.getUpperFluxBound()
    p_ub = model.getParameter(pid_ub)
    assert p_ub
    assert p_ub.value == builder.UPPER_BOUND_DEFAULT
    pid_lb = fbc_ex_B.getLowerFluxBound()
    p_lb = model.getParameter(pid_lb)
    assert p_lb
    assert p_lb.value == builder.ZERO_BOUND


def test_create_dt():
    doc = create_fba_doc()
    model = doc.getModel()

    builder.create_dfba_dt(model, create_port=True)
    dt = model.getParameter('dt')
    assert dt
    assert dt.getConstant()
    assert dt.getSBOTermID() == builder.DT_SBO


