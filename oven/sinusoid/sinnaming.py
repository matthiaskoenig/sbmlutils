"""
Naming functions for sinusoidal unit.

Definition of identifiers and names for species in the model.
General set of helper functions to work naming and identifier issues in the models.

The periportal compartment PP goes directly in the sinusoidal compartment S01,
which is adjacent to the Disse Space D01 and the hepatocyte H01.
The internal hepatocyte compartments are C01 (cytosol), ..., depending on the
actual model.
In total Nc (20) hepatocytes and adjacent Disse and sinusoidal compartments are
in the geometry.

---------------------------
 PP | S01 | ... | SNc | PV    Sinusoid
---------------------------
    | D01 | ... | DNc |       Space of Disse
    -------------------
    | H01 | ... | H20 |       Hepatocyte &
    | C01 | ... | C20 |       subcellular compartments.
    | ... | ... | ... |
    -------------------
"""
from __future__ import print_function, absolute_import
from six import iteritems
import re


# -------------------------------------------------------------------------------------
# Compartments
# -------------------------------------------------------------------------------------

def getPPId():
    return 'PP'


def getPVId():
    return 'PV'


def getSinusoidId(k):
    return 'S{:0>2d}'.format(k)


def getDisseId(k):
    return 'D{:0>2d}'.format(k)


def getHepatocyteId(k):
    return 'H{:0>2d}'.format(k)


def getCytosolId(k):
    return 'C{:0>2d}'.format(k)


def getPPName():
    return '[{}] periportal'.format(getPPId())


def getPVName():
    return '[{}] perivenious'.format(getPVId())


def getSinusoidName(k):
    return '[{}] sinusoid'.format(getSinusoidId(k))


def getDisseName(k):
    return '[{}] disse'.format(getDisseId(k))


def getHepatocyteName(k):
    return '[{}] hepatocyte'.format(getHepatocyteId(k))


def getCytosolName(k):
    return '[{}] cytosol'.format(getCytosolId(k))


# -------------------------------------------------------------------------------------
# Species
# -------------------------------------------------------------------------------------
SEPARATOR = "__"
NONE_ID = 'NONE'


def createLocalizedId(cid, sid):
    """ Create a compartmentalized id by concatenation. """
    return SEPARATOR.join([cid, sid])


def isLocalizedId(c_pattern, test_id):
    """ Test if test_id starts with the given compartment pattern followed by
        separator.
        re.match() determines if the RE matches at the beginning of the string
        and returns None of no match can be found

    """
    match = re.match('^{}{}'.format(c_pattern, SEPARATOR), test_id)
    return match is not None


def getSpeciesFromLocalizedId(loc_id):
    tokens = loc_id.split(SEPARATOR)
    return tokens[1]


def isPPSpeciesId(test_id):
    return isLocalizedId(getPPId(), test_id)


def getPPSpeciesId(sid):
    return createLocalizedId(getPPId(), sid)


def isPVSpeciesId(test_id):
    return isLocalizedId(getPVId(), test_id)


def getPVSpeciesId(sid):
    return createLocalizedId(getPVId(), sid)


def isSinusoidSpeciesId(test_id):
    return isLocalizedId('S(\d){2}', test_id)


def getSinusoidSpeciesId(sid, k):
    return createLocalizedId(getSinusoidId(k), sid)


def isDisseSpeciesId(test_id):
    return isLocalizedId('D(\d){2}', test_id)


def getDisseSpeciesId(sid, k):
    return createLocalizedId(getDisseId(k), sid)


def isHepatocyteSpeciesId(test_id):
    return isLocalizedId('H(\d){2}', test_id)


def getHepatocyteSpeciesId(sid, k):
    return createLocalizedId(getHepatocyteId(k), sid)


def isCytosolSpeciesId(test_id):
    return isLocalizedId('C(\d){2}', test_id)


def getCytosolSpeciesId(sid, k):
    return createLocalizedId(getCytosolId(k), sid)


def getPPSpeciesName(name):
    return '[{}] {}'.format(getPPId(), name)


def getPVSpeciesName(name):
    return '[{}] {}'.format(getPVId(), name)


def getSinusoidSpeciesName(name, k):
    return '[{}] {}'.format(getSinusoidId(k), name)


def getDisseSpeciesName(name, k):
    return '[{}] {}'.format(getDisseId(k), name)


def getHepatocyteSpeciesName(name, k):
    return '[{}] {}'.format(getHepatocyteId(k), name)


def getCytosolSpeciesName(name, k):
    return '[{}] {}'.format(getHepatocyteId(k), name)


# -------------------------------------------------------------------------------------
# Reaction helpers
# -------------------------------------------------------------------------------------
def getTemplateId(pid, sid1, sid2):
    if not sid2:
        # returns the midpoint position id of the volume
        return '{}_{}'.format(sid1, pid)
    else:
        # returns the between position id for two volumes
        return '{}{}_{}'.format(sid1, sid2, pid)


# Parameters (position, pressure, flow)
def getPositionId(sid1, sid2=None):
    return getTemplateId('x', sid1, sid2)


def getPressureId(sid1, sid2=None):
    return getTemplateId('P', sid1, sid2)


def getqFlowId(sid1, sid2=None):
    return getTemplateId('q', sid1, sid2)


def getQFlowId(sid1, sid2=None):
    return getTemplateId('Q', sid1, sid2)


# Reactions
def createFlowId(c_from, c_to, sid):
    return 'F_{}{}_{}'.format(c_from, c_to, sid)


def createFlowName(c_from, c_to, sid):
    if c_to == NONE_ID:
        c_to = ''
    return '[{} -> {}] convection {}'.format(c_from, c_to, sid)


def createDiffusionId(c_from, c_to, sid):
    return 'D_{}{}_{}'.format(c_from, c_to, sid)


def createDiffusionName(c_from, c_to, sid):
    if c_to == NONE_ID:
        c_to = ''
    return '[{} <-> {}] diffusion {}'.format(c_from, c_to, sid)


# -------------------------------------------------------------------------------------
# Initialization helpers
# -------------------------------------------------------------------------------------
def initString(s, initDict):
    """ Initializes the string with the given data dictionary.
        Makes a copy to allow multiple initializations with
        differing data.
    """
    # assert isinstance(s, str)
    if not isinstance(s, str):
        return s

    # handle the case of no replacements
    if len(initDict) is 0:
        return s

    # replace everything from the dict
    res = s[:]
    for key, value in iteritems(initDict):
        res = res.replace(key, value)
    return res
