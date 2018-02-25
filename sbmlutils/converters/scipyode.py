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
from sbmlutils.converters.mathml import evaluableMathML

def f_ode(sbml_file, py_file):
    """ Create ode system which can be integrated with scipy.
    The python module is stored.

    :param sbml_file:
    :return:
    """
    print(sbml_file)
    doc = libsbml.readSBMLFromFile(sbml_file)  # type: libsbml.SBMLDocument
    model = doc.getModel()  # type: libsbml.Model

    x0 = {}
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
            value = ''
        pids[pid] = value

    # --------------
    # species
    # --------------
    for species in model.getListOfSpecies():  # type: libsbml.Species
        sid = species.getId()
        xids[sid] = ''



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
            astnode = rate_rule.getMath()
            xids[variable] = evaluableMathML(astnode)

            # could be species or variable
            if variable in pids:
                del pids[variable]

        # --------------
        # assignment rules
        # --------------
        elif type_code == libsbml.SBML_ASSIGNMENT_RULE:
            as_rule = rule  # type: libsbml.RateRule
            variable = as_rule.getVariable()
            astnode = as_rule.getMath()
            yids[variable] = evaluableMathML(astnode)
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
            astnode = klaw.getMath()
            formula = evaluableMathML(astnode)
        rids[rid] = formula
        for reactant in reaction.getListOfReactants():  # type: libsbml.SpeciesReference
            stoichiometry = reactant.getStoichiometry()
            sid = reactant.getSpecies()
            species = model.getSpecies(sid)
            vid = species.getCompartment()

            # check if only substance units
            if species.getHasOnlySubstanceUnits():
                xids[sid] += ' - {}*({})'.format(stoichiometry, formula)
            else:
                xids[sid] += '- {}*({})/{}'.format(stoichiometry, formula, vid)
        for product in reaction.getListOfProducts():  # type: libsbml.SpeciesReference
            stoichiometry = product.getStoichiometry()
            sid = product.getSpecies()
            species = model.getSpecies(sid)
            vid = species.getCompartment()

            # check if only substance units
            if species.getHasOnlySubstanceUnits():
                xids[sid] += ' + {}*({})'.format(stoichiometry, formula)
            else:
                xids[sid] += ' + {}*({})/{}'.format(stoichiometry, formula, vid)


    with open(py_file, "w") as f:
        empty_line = "# " + '-'*80 + "\n"

        for vid, d in [('x', xids), ('r', rids), ('p', pids), ('y', yids)]:
            f.write(empty_line)
            f.write("# " + vid + "\n")
            f.write(empty_line)

            f.write("{} = [\n".format(vid))
            for key in sorted(d.keys()):
                f.write('    {},\t\t# {}\n'.format(d[key], key))
            f.write("]\n\n")

    # TODO: necessary to find dependency tree for yids (order accordingly)
    # check which math depends on other math (build tree of dependencies)








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
    model_id = "limax_pkpd_38"
    in_dir = './scipyode_example'
    out_dir = './scipyode_example/results'
    sbml_file = os.path.join(in_dir, "{}.xml".format(model_id))
    py_file = os.path.join(in_dir, "{}.py".format(model_id))


    f = f_ode(sbml_file, py_file)


    # ----------------------
    # scipy simulation
    # ----------------------

    # 1. Get general information of the system, i.e.
    # states, parameters, odes, initial conditions, ...


    # 2. Change parameters & initial conditions
    # calculate all the initial conditions for the system (InitialAssignments & values for species)


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



