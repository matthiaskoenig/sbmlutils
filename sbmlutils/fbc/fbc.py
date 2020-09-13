"""
Helper functions for working with FBC and cobrapy models.
"""
import logging
import warnings
import libsbml
from sbmlutils import factory

logger = logging.getLogger(__name__)

__all__ = [
    'Objective',
]


class Objective(factory.Sbase):
    """Objective."""

    def __init__(self, sid,
                 objectiveType=libsbml.OBJECTIVE_TYPE_MAXIMIZE,
                 active=True,
                 fluxObjectives={},
                 name=None, sboTerm=None, metaId=None):
        """ Create a layout. """
        super(Objective, self).__init__(sid=sid, name=name, sboTerm=sboTerm, metaId=metaId)
        self.objectiveType = objectiveType
        self.active = active
        self.fluxObjectives = fluxObjectives

    def create_sbml(self, model: libsbml.Model):
        model_fbc = model.getPlugin("fbc")  # type: libsbml.FbcModelPlugin
        obj = model_fbc.createObjective()  # type: libsbml.Objective
        obj.setId(self.sid)
        obj.setType(self.objectiveType)
        if self.active:
            model_fbc.setActiveObjectiveId(self.sid)
        for rid, coefficient in self.fluxObjectives.items():
            # FIXME: check for rid
            fluxObjective = obj.createFluxObjective()
            fluxObjective.setReaction(rid)
            fluxObjective.setCoefficient(coefficient)
        return obj

    def set_fields(self, obj: libsbml.Layout):
        super(Objective, self).set_fields(obj)


def create_objective(model_fbc, oid, otype, fluxObjectives, active=True):
    """ Create flux optimization objective.

    :param model_fbc: FbcModelPlugin
    :param oid: objective identifier
    :param otype:
    :param fluxObjectives:
    :param active:
    :return:
    """
    objective = model_fbc.createObjective()
    objective.setId(oid)
    objective.setType(otype)
    if active:
        model_fbc.setActiveObjectiveId(oid)
    for rid, coefficient in fluxObjectives.items():
        fluxObjective = objective.createFluxObjective()
        fluxObjective.setReaction(rid)
        fluxObjective.setCoefficient(coefficient)
    return objective


# -----------------------------------------------------------------------------
# FluxBounds
# -----------------------------------------------------------------------------
def set_flux_bounds(reaction: libsbml.Reaction, lb: float, ub: float) -> None:
    """ Set flux bounds on given reaction. """
    rplugin = reaction.getPlugin("fbc")
    rplugin.setLowerFluxBound(lb)
    rplugin.setUpperFluxBound(ub)


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
