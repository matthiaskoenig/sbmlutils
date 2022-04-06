"""Helper functions for working with FBC and cobrapy models."""
import warnings

import libsbml

from sbmlutils import log


logger = log.get_logger(__name__)


def set_flux_bounds(reaction: libsbml.Reaction, lb: float, ub: float) -> None:
    """Set flux bounds on given reaction."""
    rplugin = reaction.getPlugin("fbc")
    rplugin.setLowerFluxBound(lb)
    rplugin.setUpperFluxBound(ub)


def add_default_flux_bounds(
    doc: libsbml.SBMLDocument, lower: float = -100.0, upper: float = 100.0
) -> None:
    """Add default flux bounds to SBMLDocument.

    :param doc: SBMLDocument
    :param lower: lower flux bound
    :param upper: upper flux bound
    :return:
    """
    model = doc.getModel()

    def create_bound(sid: str, value: float) -> libsbml.Parameter:
        """Create flux bound parameter with given value.

        :param sid: id of parameter
        :param value: flux bound
        :return:
        """
        p = model.createParameter()
        p.setId(sid)
        p.setValue(value)
        p.setName("{} flux bound".format(sid))
        p.setSBOTerm("SBO:0000626")  # default flux bound
        p.setConstant(True)
        return p

    # FIXME: overwrites lower/upper parameter (you should check if existing in model)
    create_bound(sid="lower", value=lower)
    create_bound(sid="upper", value=upper)

    for r in model.reactions:
        rfbc = r.getPlugin("fbc")
        if not rfbc.isSetLowerFluxBound():
            rfbc.setLowerFluxBound("lower")
        if not rfbc.isSetUpperFluxBound():
            rfbc.setUpperFluxBound("upper")


def no_boundary_conditions(doc: libsbml.SBMLDocument) -> None:
    """Set all boundaryCondition to False in the model.

    :param doc: libsbml.SBMLDocument
    :return:
    """
    model = doc.getModel()
    for s in model.species:
        if s.boundary_condition:
            warnings.warn("boundaryCondition changed {}".format(s), UserWarning)
            s.setBoundaryCondition(False)
