"""
Working with fbc models.
"""
from __future__ import print_function, division
import cobra
import libsbml
from warnings import warn
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
    add_default_flux_bounds(doc)

    # boundarySpecies
    no_boundary_conditions(doc)

    import tempfile
    f = tempfile.NamedTemporaryFile('w', suffix='xml')
    libsbml.writeSBMLToFile(doc, f.name)
    f.flush()
    model = cobra.io.read_sbml_model(f.name)
    return model


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
    warn('Adding default flux bounds', UserWarning)
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


def no_boundary_conditions(doc):
    """ Sets all boundaryCondition to False in the model.

    :param doc:
    :type doc:
    :return:
    :rtype:
    """
    model = doc.getModel()
    for s in model.species:
        if s.boundary_condition == True:
            warn('boundaryCondition changed {}'.format(s), UserWarning)
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


if __name__ == "__main__":
    """
    Example for creation of fbc model.

    Extension package information is set via getting the
    respective plugins from the core model.
    """
    from libsbml import *

    sbmlns = SBMLNamespaces(3, 1, "fbc", 2)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("fbc", False)
    model = doc.createModel()
    mplugin = model.getPlugin("fbc")
    mplugin.setStrict(False)

    s = model.createSpecies()
    s.setId('S1')
    sfbc = s.getPlugin('fbc')
    sfbc.setChemicalFormula('H2O')

    sbml_str = writeSBMLToString(doc)
    print(sbml_str)
