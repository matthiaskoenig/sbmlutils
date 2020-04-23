import logging
import libsbml
import datetime


def date_now() -> libsbml.Date:
    """ Get current time stamp for history.

    :return: current libsbml Date
    """
    time = datetime.datetime.now()
    timestr = time.strftime('%Y-%m-%dT%H:%M:%S')
    return libsbml.Date(timestr)


def check(value, message):
    """ Checks the libsbml return value and prints message if something happened.

    If 'value' is None, prints an error message constructed using
      'message' and then exits with status code 1. If 'value' is an integer,
      it assumes it is a libSBML return status code. If the code value is
      LIBSBML_OPERATION_SUCCESS, returns without further action; if it is not,
      prints an error message constructed using 'message' along with text from
      libSBML explaining the meaning of the code, and exits with status code 1.

    """
    if value is None:
        logging.error('Error: LibSBML returned a null value trying to <' + message + '>.')
    elif type(value) is int:
        if value == libsbml.LIBSBML_OPERATION_SUCCESS:
            return
        else:
            logging.error('Error encountered trying to <' + message + '>.')
            logging.error('LibSBML returned error code {}: {}'.format(str(value),
                          libsbml.OperationReturnValue_toString(value).strip()))
    else:
        return


def set_model_history(sbase, creators, set_timestamps=True):
    """Set a model history with given creators."""
    h = libsbml.ModelHistory()  # type: libsbml.ModelHistory

    # add creators
    for creator in creators:
        c = libsbml.ModelCreator()
        if creator.familyName:
            c.setFamilyName(creator.familyName)
        if creator.givenName:
            c.setGivenName(creator.givenName)
        if creator.email:
            c.setEmail(creator.email)
        if creator.organization:
            c.setOrganization(creator.organization)
        check(h.addCreator(c), 'add creator')


    if set_timestamps:
        datetime = date_now()
    else:
        datetime = libsbml.Date('1900-01-01T00:00:00')
    check(h.setCreatedDate(datetime), 'set creation date')
    check(h.setModifiedDate(datetime), 'set modified date')


    check(sbase.setModelHistory(h), f'set model history on {sbase}')


class Creator(object):
    """ Creator in ModelHistory. """
    def __init__(self, familyName, givenName, email, organization, site=None):
        self.familyName = familyName
        self.givenName = givenName
        self.email = email
        self.organization = organization
        self.site = site


if __name__ == "__main__":
    creators = [
        Creator(familyName='Koenig',
                givenName='Matthias',
                email='koenigmx@hu-berlin.de',
                organization='Humboldt-University Berlin, Institute for Theoretical Biology',
                site="https://livermetabolism.com")
    ]

    doc = libsbml.SBMLDocument()  # type: libsbml.SBMLDocument
    model = doc.createModel()  # type: libsbml.Model
    model.setId("model1")
    p1 = model.createParameter()  # type: libsbml.Parameter
    p1.setId("p1")
    p1.setMetaId("meta_p1")

    p2 = model.createParameter()  # type: libsbml.Parameter
    p2.setId("p2")
    p2.setMetaId("meta_p2")

    # set history with timesteps
    set_model_history(p1, creators=creators, set_timestamps=True)
    # set history without timestamps
    set_model_history(p2, creators=creators, set_timestamps=False)
