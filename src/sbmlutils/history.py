"""Handle manipulation of the History of SBases."""
import datetime
from typing import Any, Dict, List, Union

import libsbml

from sbmlutils.utils import create_metaid
from sbmlutils.validation import check


def date_now() -> libsbml.Date:
    """Get current time stamp for history.

    :return: current libsbml Date
    """
    time = datetime.datetime.now()
    timestr = time.strftime("%Y-%m-%dT%H:%M:%S")
    return libsbml.Date(timestr)


def set_model_history(model: libsbml.Model, creators: Union[List, Dict]) -> None:
    """Set the model history from given creators.

    :param model: SBML model
    :param creators: list of creators
    :return:
    """
    if not model.isSetMetaId():
        model.setMetaId(create_metaid(sbase=model))

    if (creators is None) or (len(creators) == 0):
        # at least on
        return
    else:
        # create and set model history
        h = _create_history(creators)
        check(model.setModelHistory(h), "set model history")


def _create_history(
    creators: Union[List[Any], Dict[Any, Any]], set_timestamps: bool = False
) -> libsbml.ModelHistory:
    """Create the model history.

    Sets the create and modified date to the current time.
    Creators are a list or dictionary with values as

    :param creators:
    :param set_timestamps:
    :return:
    """
    h = libsbml.ModelHistory()

    items: List[Any]
    if isinstance(creators, dict):
        items = list(creators.values())
    else:
        items = creators

    # add all creators
    for creator in items:
        c = libsbml.ModelCreator()
        if creator.familyName:
            c.setFamilyName(creator.familyName)
        if creator.givenName:
            c.setGivenName(creator.givenName)
        if creator.email:
            c.setEmail(creator.email)
        if creator.organization:
            c.setOrganization(creator.organization)
        check(h.addCreator(c), "add creator")

    # create time is now
    if set_timestamps:
        datetime = date_now()
    else:
        datetime = libsbml.Date("1900-01-01T00:00:00")
    check(h.setCreatedDate(datetime), "set creation date")
    check(h.setModifiedDate(datetime), "set modified date")

    return h
