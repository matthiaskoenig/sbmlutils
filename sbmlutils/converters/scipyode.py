"""
Convert SBML model to ODE system which can be integrated with scipy.
"""
import os
import numpy as np
from scipy.integrate import odeint
from matplotlib import pyplot as plt
try:
    import libsbml
except ImportError:
    import tesbml as libsbml

from pprint import pprint


def f_ode(sbml_file):
    """ Create ode system which can be integrated with scipy.

    :param sbml_file:
    :return:
    """
    print(sbml_file)
    doc = libsbml.readSBMLFromFile(sbml_file)  # type: libsbml.SBMLDocument
    model = doc.getModel()  # type: libsbml.Model

    xids = {}  # state variables x
    pids = {}  # parameters p
    yids = {}  # assigned variables
    rids = {}

    # --------------
    # parameters
    # --------------
    # 1. constant parameters (real parameters of the system)
    for parameter in model.getListOfParameters():  # type: libsbml.Parameter
        pid = parameter.getId()
        if parameter.getConstant():
            value = parameter.getValue()
        else:
            value = None
        pids[pid] = value

    # --------------
    # species
    # --------------
    for species in model.getListOfSpecies():  # type: libsbml.Species
        sid = species.getId()
        xids[sid] = None

    # SBML_ASSIGNMENT_RULE = _libsbml.SBML_ASSIGNMENT_RULE
    # SBML_RATE_RULE = _libsbml.SBML_RATE_RULE
    # SBML_SPECIES_CONCENTRATION_RULE = _libsbml.SBML_SPECIES_CONCENTRATION_RULE

    for rule in model.getListOfRules():  # type: libsbml.Rule

        type_code = rule.getTypeCode()
        # --------------
        # rate rules
        # --------------
        if type_code == libsbml.SBML_RATE_RULE:
            # directly converted to odes (create additional state variables)
            rate_rule = rule  # type: libsbml.RateRule
            variable = rate_rule.getVariable()

            # store rule
            math = rate_rule.getMath()
            xids[variable] = math

            # could be species or variable
            if variable in pids:
                del pids[variable]

        # --------------
        # assignment rules
        # --------------
        elif type_code == libsbml.SBML_ASSIGNMENT_RULE:
            as_rule = rule  # type: libsbml.RateRule
            variable = as_rule.getVariable()
            math = as_rule.getMath()
            yids[variable] = math
            if variable in xids:
                del xids[variable]
            if variable in pids:
                del pids[variable]

    # Process the kinetic laws of reactions
    for reaction in model.getListOfReactions():  # type: libsbml.Reaction
        rid = reaction.getId()
        math = None
        if reaction.isSetKineticLaw():
            klaw = reaction.getKineticLaw()  # type: libsbml.KineticLaw
            math = klaw.getMath()
        rids[rid] = math

    print("-"*80)
    print('xids')
    print("-" * 80)
    pprint(xids)

    print("-" * 80)
    print('pids')
    print("-" * 80)
    pprint(pids)

    print("-" * 80)
    print('yids')
    print("-" * 80)
    pprint(yids)

    # TODO: necessary to find dependency tree for yids






    # handle initial assignments

    # -----------------
    # assignment rules
    # -----------------
    # def y(x, t):




    def fdxdt(x, t, p):

        # calculate y values which are depending on x and p and possible other y (in order of dependency
        # y =



        # calculate the next differential equation
        c = 1.0
        k = 2.0
        dxdt = c - k * x
        return dxdt

    return x, xids, p, pids, fdxdt


if __name__ == "__main__":

    # convert xpp to sbml
    model_id = "limax_pkpd_37"
    in_dir = './scipyode_example'
    out_dir = './scipyode_example/results'
    sbml_file = os.path.join(in_dir, "{}.xml".format(model_id))


    f = f_ode(sbml_file)


    # ----------------------
    # scipy simulation
    # ----------------------

    # 1. Get general information of the system, i.e.
    # states, parameters, odes, initial conditions, ...


    # 2. Change parameters & initial conditions


    # 3. Update initial conditions based on changed parameters (apply InitialAssignment rules)



    # 4. perform integration
    # intital condition and timespan
    T = np.arange(0, 10, 0.1)
    X0 = 0
    X = odeint(f, X0, T)

    # Calculate y values used in differential equations

    # Calculate y values not used in differential equations



    plt.plot(T, X, linewidth=2)
    plt.show()



