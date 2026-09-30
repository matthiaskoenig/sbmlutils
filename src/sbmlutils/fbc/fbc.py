"""Helper functions for working with FBC and cobrapy models."""

import logging

import libsbml

logger = logging.getLogger(__name__)


def add_default_flux_bounds(
    doc: libsbml.SBMLDocument, lower: float = -100.0, upper: float = 100.0
) -> None:
    """Add default flux bounds to SBMLDocument.

    The bounds are the parameters `lower` and `upper`, which are set on every
    reaction without a bound. An id which exists in the model already is kept
    as it is, the bound then gets the first free id `lower_1`, `lower_2`, ...

    :param doc: SBMLDocument
    :param lower: lower flux bound
    :param upper: upper flux bound
    :return:
    """
    model: libsbml.Model = doc.getModel()

    def create_bound(sid: str, value: float) -> str:
        """Create flux bound parameter with given value.

        Args:
            sid: preferred id of the parameter
            value: flux bound

        Returns:
            the id of the created parameter, `sid` or the first free
            `<sid>_<k>`
        """
        bound_id = sid
        k = 0
        while model.getElementBySId(bound_id) is not None:
            k += 1
            bound_id = f"{sid}_{k}"

        p: libsbml.Parameter = model.createParameter()
        p.setId(bound_id)
        p.setValue(value)
        p.setName(f"{bound_id} flux bound")
        p.setSBOTerm("SBO:0000626")  # default flux bound
        p.setConstant(True)
        return bound_id

    lower_id = create_bound(sid="lower", value=lower)
    upper_id = create_bound(sid="upper", value=upper)

    for k in range(model.getNumReactions()):
        rfbc = model.getReaction(k).getPlugin("fbc")
        if not rfbc.isSetLowerFluxBound():
            rfbc.setLowerFluxBound(lower_id)
        if not rfbc.isSetUpperFluxBound():
            rfbc.setUpperFluxBound(upper_id)
