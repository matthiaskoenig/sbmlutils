"""
Utility functions.
"""
import warnings
import time
import libsbml
import functools
import uuid



def create_metaid(sbase):
    """ Creates a unique meta id.

    Meta ids are required to store annotation elements.
    """
    hash_id = _create_hash_id(sbase)
    return 'meta_{}'.format(hash_id)


def _create_hash_id(sbase):
    """ Creates unique hash id for sbase in model.

    :param sbase:
    :return:
    """
    # FIXME: This must be reproducible, so models don't change on recreation
    if sbase and hasattr(sbase, 'getId') and sbase.isSetId():
        hash_id = sbase.getId()
    else:
        hash_id = uuid.uuid4().hex

    # the special case of the assignment rules (getId() returns getVariable())
    if isinstance(sbase, libsbml.AssignmentRule) or isinstance(sbase, libsbml.RateRule):
        hash_id = uuid.uuid4().hex
    return hash_id





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


def deprecated(func):
    """This is a decorator which can be used to mark functions
        as deprecated. It will result in a warning being emitted
        when the function is used.
    """
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn_explicit(
            "Call to deprecated function {}.".format(func.__name__),
            category=DeprecationWarning,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1
        )
        return func(*args, **kwargs)
    return new_func


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
