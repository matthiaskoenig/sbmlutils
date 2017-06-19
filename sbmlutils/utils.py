from __future__ import print_function, absolute_import
import warnings
import time
import libsbml

def timeit(f):
    """ Timing decorator.

    :param f: function to time
    :return:
    """
    def timed(*args, **kw):

        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        print('func:%r args:[%r, %r] took: %2.4f sec' % (f.__name__, args, kw, te-ts))
        return result

    return timed


def promote_local_variables(doc):
    """ Promotes local variables in SBMLDocument.

    :param doc:
    :return:
    """
    model = doc.getModel()
    mid = model.id
    mid = '{}_{}'.format(mid, 'promoted')
    model.setId(mid)

    # promote local parameters
    props = libsbml.ConversionProperties()
    props.addOption("promoteLocalParameters", True, "Promotes all Local Parameters to Global ones")
    if doc.convert(props) != libsbml.LIBSBML_OPERATION_SUCCESS:
        warnings.warn("SBML Conversion failed...")
    else:
        print("SBML Conversion successful")
    return doc
