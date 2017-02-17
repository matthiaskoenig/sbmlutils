####################################################
# ODE flux bounds
####################################################
def create_ode_bounds(sbml_file, directory):
    """"
    Submodel for dynamically calculating the flux bounds.
    The dynamically changing flux bounds are the input to the
    FBA model.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    model = doc.createModel()
    model.setId("toy_ode_bounds")
    model.setName("ODE bound calculation submodel")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    objects = [
        # parameters
        mc.Parameter(sid='ub_R1', value=1.0, unit=UNIT_FLUX, name='ub_r1', constant=False),
        mc.Parameter(sid='k1', value=-0.2, unit="per_s", name="k1", constant=False),

        # rate rules
        mc.RateRule(sid="ub_R1", value="k1*ub_R1")
    ]
    mc.create_objects(model, objects)

    # ports
    comp._create_port(model, pid="ub_R1_port", idRef="ub_R1", portType=comp.PORT_TYPE_PORT)

    sbml_io.write_and_check(doc, os.path.join(directory, sbml_file))


####################################################
# ODE species update
####################################################
def create_ode_update(sbml_file, directory):
    """
        Submodel for dynamically updating the metabolite count.
        This updates the ode model based on the FBA fluxes.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    # model
    model = doc.createModel()
    model.setId("toy_ode_update")
    model.setName("ODE metabolite update submodel")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    compartments = [
        mc.Compartment(sid='extern', value=1.0, unit="m3", constant=True, name='external compartment', spatialDimension=3),
    ]
    mc.create_objects(model, compartments)

    # only update the boundarySpecies in the reactions
    species = [
        mc.Species(sid='C', name="C", value=0, unit=UNIT_AMOUNT, hasOnlySubstanceUnits=True,
                   compartment="extern", boundaryCondition=False),
    ]
    mc.create_objects(model, species)

    parameters = [
        mc.Parameter(sid="vR3", name="vR3 (FBA flux)", value=0.1, constant=True, unit="item_per_s"),
    ]
    mc.create_objects(model, parameters)

    # kinetic reaction (MMK)
    mc.create_reaction(model, rid="R3", name="-> C", fast=False, reversible=False,
                       reactants={}, products={"C": 1}, formula="vR3", compartment="extern")

    comp._create_port(model, pid="vR3_port", idRef="vR3", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="C_port", idRef="C", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="extern_port", idRef="extern", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_and_check(doc, os.path.join(directory, sbml_file))


####################################################
# ODE/SSA model
####################################################
def create_ode_model(sbml_file, directory):
    """" Kinetic submodel (coupled model to FBA).
    Describing the change in the batch bioreactor.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)

    # model
    model = doc.createModel()
    model.setId("diauxic_ode")
    model.setName("diauxic ODE submodel")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    compartments = [
        mc.Compartment(sid='bioreactor', value=1.0, unit="m3", constant=True, name='external compartment', spatialDimension=3),
    ]
    mc.create_objects(model, compartments)

    species = [
        # external
        mc.Species(sid='Glcxt', name="glucose", value=11, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor", boundaryCondition=False),
        mc.Species(sid='O2', name="oxygen", value=0.21, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor", boundaryCondition=False),
        mc.Species(sid='Ac', name="acetate", value=0.5, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor", boundaryCondition=False),
        mc.Species(sid='X', name="biomass", value=0, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor", boundaryCondition=False),
    ]
    mc.create_objects(model, species)

    parameters = [
        mc.Parameter(sid="A_Glcxt", name="k R4", value=0.1, constant=True, unit="per_s"),
    ]
    mc.create_objects(model, parameters)

    # kinetic reaction (MMK)
    mc.create_reaction(model, rid="R4", name="C -> D", fast=False, reversible=False,
                       reactants={"C": 1}, products={"D": 1}, formula="k_R4*C", compartment="extern")

    comp._create_port(model, pid="C_port", idRef="C", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="extern_port", idRef="extern", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_and_check(doc, os.path.join(directory, sbml_file))
