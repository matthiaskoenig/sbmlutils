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

import re
from pprint import pprint
from sbmlutils.converters.mathml import evaluableMathML
from collections import defaultdict

# TODO: create class for SBML to ODE conversion


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
    dxids = {}  # state variables x
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
        dxids[sid] = ''

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
            rate_rule = rule  # type: libsbml.AssignmentRule
            variable = rate_rule.getVariable()

            # store rule
            astnode = rate_rule.getMath()
            dxids[variable] = astnode
            # dxids[variable] = evaluableMathML(astnode)

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
            yids[variable] = astnode
            # yids[variable] = evaluableMathML(astnode)
            if variable in dxids:
                del dxids[variable]
            if variable in pids:
                del pids[variable]


    def add_reaction_formula(rid, species_ref, sign):
        """ Adds part of reaction formula to species.
        :param rid:
        :param species_ref:
        :param sign:
        :return:
        """
        stoichiometry = species_ref.getStoichiometry()
        sid = species_ref.getSpecies()
        species = model.getSpecies(sid)
        vid = species.getCompartment()

        # stoichiometry prefix
        if abs(stoichiometry - 1.0) < 1E-10:
            stoichiometry = ''
        else:
            stoichiometry = '{}*'.format(stoichiometry)

        # check if only substance units
        if species.getHasOnlySubstanceUnits():
            dxids[sid] += ' {} {}{}'.format(sign, stoichiometry, rid)
        else:
            dxids[sid] += ' {} {}{}/{}'.format(sign, stoichiometry, rid, vid)

    # Process the kinetic laws of reactions
    for reaction in model.getListOfReactions():  # type: libsbml.Reaction
        rid = reaction.getId()
        formula = None  # fallback
        if reaction.isSetKineticLaw():
            klaw = reaction.getKineticLaw()  # type: libsbml.KineticLaw
            astnode = klaw.getMath()
        rids[rid] = astnode

        for reactant in reaction.getListOfReactants():  # type: libsbml.SpeciesReference
            add_reaction_formula(rid=rid, species_ref=reactant, sign="-")
        for product in reaction.getListOfProducts():  # type: libsbml.SpeciesReference
            add_reaction_formula(rid=rid, species_ref=product, sign="+")


    # check which math depends on other math (build tree of dependencies)
    filtered_ids = set(list(pids.keys()) + list(dxids.keys()) + list(rids.keys()))
    yids_ordered = ordered_yids(model, filtered_ids)
    print(yids_ordered)
    print(len(yids_ordered))

    # replacement dictionaries:
    pids_idx = {}
    for k, key in enumerate(sorted(pids.keys())):
        pids_idx[key] = k
    yids_idx = {}
    for k, key in enumerate(sorted(yids_ordered)):
        yids_idx[key] = k
    dxids_idx = {}
    for k, key in enumerate(sorted(dxids.keys())):
        dxids_idx[key] = k

    pprint(pids_idx)


    for d in [yids, rids, dxids]:
        # y: replace p and x, y
        for key in d:
            astnode = d[key]
            if not isinstance(astnode, libsbml.ASTNode):
                continue

            # replace parameters
            for key_rep, index in pids_idx.items():
                ast_rep = libsbml.parseL3Formula('p__{}__'.format(index))
                astnode.replaceArgument(key_rep, ast_rep)
            # replace states
            for key_rep, index in dxids_idx.items():
                ast_rep = libsbml.parseL3Formula('x__{}__'.format(index))
                astnode.replaceArgument(key_rep, ast_rep)
            # replace y
            for key_rep, index in yids_idx.items():
                ast_rep = libsbml.parseL3Formula('y__{}__'.format(index))
                astnode.replaceArgument(key_rep, ast_rep)

            formula = evaluableMathML(astnode)
            # TODO: perform replacements with indices
            formula = re.sub("p__", "p[", formula)
            formula = re.sub("x__", "x[", formula)
            formula = re.sub("y__", "y[", formula)
            formula = re.sub("__", "]", formula)

            d[key] = formula

    # ------------------------
    # Write ODE
    # ------------------------

    with open(py_file, "w") as f:



        # write states, reactions, pids
        for vid, d in [('p', pids)]:
            f.write("{} = [\n".format(vid))
            for key in sorted(d.keys()):
                f.write('    {},\t\t# {}\n'.format(d[key], key))
            f.write("]\n\n")


        # write ode function
        f.write("def f_dxdt(x, t, p):\n")
        f.write('    """ ODE system """\n')

        # y
        f.write("    {} = [\n".format('y'))
        for key in yids_ordered:
            f.write('        {},\t\t# {}\n'.format(yids[key], key))
        f.write("    ]\n\n")

        # r
        f.write("    # reactions\n")
        for key in sorted(rids.keys()):
            f.write('    {} = {}\n'.format(key, rids[key]))
        f.write("\n\n")


        f.write("    return [\n")
        for key in sorted(dxids.keys()):
            f.write('        {},\t\t# {}\n'.format(dxids[key], key))
        f.write("    ]\n\n")

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


def ordered_yids(model, filtered_ids):
    """ Get the order of the vids from the assignment rules.

    :param model:
    :param filtered_ids
    :return:
    """
    g = defaultdict(set)

    def add_dependency_edges(g, astnode):
        """ Add the dependency edges to the graph.

        :param g:
        :param astnode:
        :return:
        """
        # variable --depends_on--> v2
        for k in range(astnode.getNumChildren()):
            child = astnode.getChild(k)  # type: libsbml.ASTNode
            if child.getType() == libsbml.AST_NAME:

                # add to dependency graph if id is not a defined parameter or state variable
                sid = child.getName()
                if sid not in filtered_ids:
                    g[variable].add(sid)

            # recursive adding of children
            add_dependency_edges(g, child)

    # create dependency graph
    for rule in model.getListOfRules():  # type: libsbml.Rule
        # assignment rules
        type_code = rule.getTypeCode()
        if type_code == libsbml.SBML_ASSIGNMENT_RULE:
            as_rule = rule  # type: libsbml.AssignmentRule
            variable = as_rule.getVariable()
            g[variable] = set()

            # traverse astnode to find the dependencies (add to graph)
            astnode = as_rule.getMath()  # type: libsbml.ASTNode
            add_dependency_edges(g, astnode)

    def create_ordered_variables(g, yids=None):
        if yids is None:
            yids = []

        yids_remove = []
        for yid in sorted(g.keys()):
            yid_deps = g[yid]

            # add yids with no dependencies
            if len(yid_deps) == 0:
                yids_remove.append(yid)

        # add nodes with no dependencies to list
        yids = yids + list(yids_remove)  # hard copy to store

        for yid in yids_remove:
            # remove the yid from nodes
            del g[yid]
            # remove the yid from dependency graph
            for s in g.values():
                if yid in s:
                    s.remove(yid)

        # still nodes in dependency graph (recursive removal)
        print(len(yids))
        print(len(g))
        if len(g) > 0:
            yids = create_ordered_variables(g, yids=yids)
        return yids

    # create order from dependency graph
    yids = create_ordered_variables(g)
    return yids


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



