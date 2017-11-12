from __future__ import absolute_import, print_function

def test_modelcreator_notebook():
    """
    If this test fails the respective notebook must be updated:
    :return:
    """

    from sbmlutils import comp
    from sbmlutils import sbmlio
    from sbmlutils import factory as fac
    from sbmlutils.dfba import builder, utils

    try:
        import libsbml
        from libsbml import (UNIT_KIND_SECOND, UNIT_KIND_ITEM, UNIT_KIND_MOLE,
                             UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_LITRE)
    except ImportError:
        import tesbml as libsbml
        from tesbml import (UNIT_KIND_SECOND, UNIT_KIND_ITEM, UNIT_KIND_MOLE,
                            UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_LITRE)

    try:
        import libsbml
        from libsbml import (UNIT_KIND_SECOND, UNIT_KIND_ITEM, UNIT_KIND_MOLE,
                             UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_LITRE)
    except ImportError:
        import tesbml as libsbml
        from tesbml import (UNIT_KIND_SECOND, UNIT_KIND_ITEM, UNIT_KIND_MOLE,
                            UNIT_KIND_KILOGRAM, UNIT_KIND_METRE, UNIT_KIND_LITRE)

    main_units = {
        'time': 's',
        'extent': UNIT_KIND_ITEM,
        'substance': UNIT_KIND_ITEM,
        'length': 'm',
        'area': 'm2',
        'volume': 'm3',
    }
    units = [
        fac.Unit('s', [(UNIT_KIND_SECOND, 1.0)]),
        fac.Unit('item', [(UNIT_KIND_ITEM, 1.0)]),
        fac.Unit('kg', [(UNIT_KIND_KILOGRAM, 1.0)]),
        fac.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
        fac.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
        fac.Unit('m3', [(UNIT_KIND_METRE, 3.0)]),
        fac.Unit('mM', [(UNIT_KIND_MOLE, 1.0, 0),
                        (UNIT_KIND_METRE, -3.0)]),
        fac.Unit('per_s', [(UNIT_KIND_SECOND, -1.0)]),
        fac.Unit('item_per_s', [(UNIT_KIND_ITEM, 1.0),
                                (UNIT_KIND_SECOND, -1.0)]),
        fac.Unit('item_per_m3', [(UNIT_KIND_ITEM, 1.0),
                                 (UNIT_KIND_METRE, -3.0)]),
    ]

    UNIT_TIME = 's'
    UNIT_AMOUNT = 'item'
    UNIT_AREA = 'm2'
    UNIT_VOLUME = 'm3'
    UNIT_CONCENTRATION = 'item_per_m3'
    UNIT_FLUX = 'item_per_s'

    # Create SBMLDocument with fba
    doc = builder.template_doc_fba(model_id="toy")
    model = doc.getModel()

    utils.set_units(model, units)
    utils.set_main_units(model, main_units)

    objects = [
        # compartments
        fac.Compartment(sid='extern', value=1.0, unit=UNIT_VOLUME, constant=True, name='external compartment',
                        spatialDimensions=3),
        fac.Compartment(sid='cell', value=1.0, unit=UNIT_VOLUME, constant=True, name='cell', spatialDimensions=3),
        fac.Compartment(sid='membrane', value=1.0, unit=UNIT_AREA, constant=True, name='membrane', spatialDimensions=2),

        # exchange species
        fac.Species(sid='A', name="A", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                    compartment="extern"),
        fac.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                    compartment="extern"),

        # internal species
        fac.Species(sid='B1', name="B1", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                    compartment="cell"),
        fac.Species(sid='B2', name="B2", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                    compartment="cell"),

        # bounds
        fac.Parameter(sid="ub_R1", value=1.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.FLUX_BOUND_SBO),
        fac.Parameter(sid="zero", value=0.0, unit=UNIT_FLUX, constant=True, sboTerm=builder.FLUX_BOUND_SBO),
        fac.Parameter(sid="ub_default", value=builder.UPPER_BOUND_DEFAULT, unit=UNIT_FLUX, constant=True,
                      sboTerm=builder.FLUX_BOUND_SBO),
    ]
    fac.create_objects(model, objects)

    # reactions
    r1 = fac.create_reaction(model, rid="R1", name="A import (R1)", fast=False, reversible=True,
                             reactants={"A": 1}, products={"B1": 1}, compartment='membrane')
    r2 = fac.create_reaction(model, rid="R2", name="B1 <-> B2 (R2)", fast=False, reversible=True,
                             reactants={"B1": 1}, products={"B2": 1}, compartment='cell')
    r3 = fac.create_reaction(model, rid="R3", name="B2 export (R3)", fast=False, reversible=True,
                             reactants={"B2": 1}, products={"C": 1}, compartment='membrane')

    # flux bounds
    fac.set_flux_bounds(r1, lb="zero", ub="ub_R1")
    fac.set_flux_bounds(r2, lb="zero", ub="ub_default")
    fac.set_flux_bounds(r3, lb="zero", ub="ub_default")

    # exchange reactions
    builder.create_exchange_reaction(model, species_id="A", flux_unit=UNIT_FLUX)
    builder.create_exchange_reaction(model, species_id="C", flux_unit=UNIT_FLUX)

    # objective function
    model_fbc = model.getPlugin("fbc")
    fac.create_objective(model_fbc, oid="R3_maximize", otype="maximize",
                         fluxObjectives={"R3": 1.0}, active=True)

    # write SBML file
    import tempfile
    sbml_file = tempfile.NamedTemporaryFile(suffix=".xml")
    sbmlio.write_sbml(doc=doc, filepath=sbml_file.name)
