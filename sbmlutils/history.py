"""
Handles manipulation of the History of SBases.
"""
from __future__ import print_function, absolute_import
import datetime
import libsbml
from six import itervalues
from sbmlutils.validation import check
from sbmlutils.annotation import create_metaid


def date_now():
    """ Get current time stamp for history.

    :return: current libsbml Date
    """
    time = datetime.datetime.now()
    timestr = time.strftime('%Y-%m-%dT%H:%M:%S')
    return libsbml.Date(timestr)


def set_model_history(model, creators):
    """ Sets the model history from given creators.

    :param model: SBML model
    :type model: libsbml.Model
    :param creators: list of creators
    :type creators:
    """
    if not model.isSetMetaId():
        model.setMetaId(create_metaid(sbase=model))

    if creators is None or len(creators) is 0:
        # at least on
        return
    else:
        # create and set model history
        h = _create_history(creators)
        check(model.setModelHistory(h), 'set model history')


def _create_history(creators):
    """ Creates the model history.

    Sets the create and modified date to the current time.
    Creators are a list or dictionary with values as
    """
    h = libsbml.ModelHistory()

    if isinstance(creators, dict):
        values = itervalues(creators)
    else:
        values = creators

    # add all creators
    for creator in values:
        c = libsbml.ModelCreator()
        c.setFamilyName(creator.familyName)
        c.setGivenName(creator.givenName)
        c.setEmail(creator.email)
        c.setOrganization(creator.organization)
        check(h.addCreator(c), 'add creator')

    # create time is now
    date = date_now()
    check(h.setCreatedDate(date), 'set creation date')
    check(h.setModifiedDate(date), 'set modified date')
    return h
