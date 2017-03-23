"""
Helper functions for working with FBC and cobrapy models.
"""
from __future__ import print_function, division, absolute_import
from six import iteritems

import warnings
import logging
import tempfile
import libsbml
import cobra

import numpy as np
import pandas as pd
from sbmlutils import factory


def load_cobra_model(sbml_path):
    """ Loads cobra model from path.
    Sets default flux bounds to allow loading and changes all boundaryConditions to False.

    :param sbml_path:
    :type sbml_path:
    :return:
    :rtype:
    """
    doc = libsbml.readSBMLFromFile(sbml_path)

    # add defaults
    # add_default_flux_bounds(doc)

    # boundarySpecies
    # no_boundary_conditions(doc)

    # f = tempfile.NamedTemporaryFile('w', suffix='xml')
    # libsbml.writeSBMLToFile(doc, f.name)
    # f.flush()
    # cobra_model = cobra.io.read_sbml_model(f.name)
    cobra_model = cobra.io.read_sbml_model(sbml_path)

    return cobra_model


def cobra_reaction_info(cobra_model):
    """ Creates data frame with bound and objective information.

    :param cobra_model:
    :return: pandas DataFrame
    """
    rids = [r.id for r in cobra_model.reactions]
    df = pd.DataFrame(data=None, index=rids,
                      columns=['lb', 'ub', 'reversibility', 'boundary', 'objective_coefficient',
                               'forward_variable', 'reverse_variable'])
    # FIXME: better filling of DataFrame
    for rid in rids:
        r = cobra_model.reactions.get_by_id(rid)

        # print('#'*80)
        # print('COBRA REACTION', r, type(r), cobra.__version__)
        # print('#' * 80)
        # import inspect
        # from pprint import pprint
        # pprint(inspect.getmembers(type(r)))

        df.loc[rid] = [r.lower_bound, r.upper_bound, r.reversibility, r.boundary, r.objective_coefficient,
                       r.forward_variable, r.reverse_variable]
    return df


def add_default_flux_bounds(doc, lower=0.0, upper=100.0, unit='mole_per_s'):
    """ Adds default flux bounds to SBMLDocument.

    :param doc:
    :type doc:
    :param lower:
    :type lower:
    :param upper:
    :type upper:
    """
    # FIXME: overwrites lower/upper parameter (check if existing)
    # TODO: the units are very specific (more generic)
    warnings.warn('Adding default flux bounds', UserWarning)
    model = doc.getModel()
    parameters = [
        factory.Parameter(sid='upper', value=upper, unit=unit),
        factory.Parameter(sid='lower', value=lower, unit=unit),
    ]
    factory.create_objects(model, parameters)
    for r in model.reactions:
        rfbc = r.getPlugin("fbc")
        if not rfbc.isSetLowerFluxBound():
            rfbc.setLowerFluxBound('lower')
        if not rfbc.isSetUpperFluxBound():
            rfbc.setUpperFluxBound('upper')


def add_default_flux_bounds(doc, lower=-100.0, upper=100.0):
    """ Adds default flux bounds to SBMLDocument.

    :param doc: SBMLDocument
    :param lower: lower flux bound
    :param upper: upper flux bound
    :return:
    """
    model = doc.getModel()

    def create_bound(sid, value):
        """ Create flux bound parameter with given value.

        :param sid: id of paramter
        :param value: flux bound
        :return:
        """
        p = model.createParameter()
        p.setId(sid)
        p.setValue(value)
        p.setName('{} flux bound'.format(sid))
        p.setSBOTerm('SBO:0000626')  # default flux bound
        p.setConstant(True)
        return p

    # FIXME: overwrites lower/upper parameter (you should check if existing in model)
    create_bound(sid='lower', value=lower)
    create_bound(sid='upper', value=upper)

    for r in model.reactions:
        rfbc = r.getPlugin("fbc")
        if not rfbc.isSetLowerFluxBound():
            rfbc.setLowerFluxBound('lower')
        if not rfbc.isSetUpperFluxBound():
            rfbc.setUpperFluxBound('upper')


def no_boundary_conditions(doc):
    """ Sets all boundaryCondition to False in the model.

    :param doc:
    :type doc:
    :return:
    :rtype:
    """
    model = doc.getModel()
    for s in model.species:
        if s.boundary_condition:
            warnings.warn('boundaryCondition changed {}'.format(s), UserWarning)
            s.setBoundaryCondition(False)


def check_balance(sbml_path):
    """Check mass and charge balance of the model.

    :param sbml_path:
    :type sbml_path:
    :return:
    :rtype:
    """
    model = load_cobra_model(sbml_path)
    # mass/charge balance
    for r in model.reactions:
        mb = r.check_mass_balance()
        if len(mb) > 0:
            print(r.id, mb, r.reaction)
