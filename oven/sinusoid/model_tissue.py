"""
Tissue model.
Similar strategy than in the CellModel.
Create the information from given module files which are imported dynamically.
"""

from libsbml import SBMLDocument, SBMLWriter
from multiscale.sbmlutils import SBMLValidator
from multiscale.sbmlutils import check
from sbmlutils.modelcreator.processes import reaction


class TissueModelException(Exception):
    pass


class TissueModel(object):
    """
    The SBML model is created from the tissue information
    and the single cell models.
    """
    _keys = ['main_units', 'units', 'names',
             'pars', 'external', 'assignments', 'rules']

    def __init__(self, Nc, Nf, version,
                 tissue_dict, cell_model, sim_id='core', events=None):
        """
        Initialize with the tissue information dictionary and
        the respective cell model used for creation.
        """
        self.Nc = Nc
        self.Nf = Nf
        self.version = version
        self.simId = sim_id
        self.cellModel = cell_model
        # print self.cellModel.info()

        # tissue information fields
        for key, value in tissue_dict.iteritems():
            setattr(self, key, value)
        self.events = events

        # sbmlutils
        self.id = self.createId()
        self.doc = SBMLDocument(SBML_LEVEL, SBML_VERSION)
        self.model = self.doc.createModel()

        check(self.model.setId(self.id), 'set id')
        check(self.model.setName(self.id), 'set name')

        # add dynamical parameters
        self.pars.extend(
            [('Nc', self.Nc, '-', True),
             ('Nf', self.Nf, '-', True), ]
        )

        print '\n', '*' * 40, '\n', self.id, '\n', '*' * 40

    @staticmethod
    def createTissueDict(module_names):
        """
        Creates one information dictionary from various modules by combining the information.
        Information in earlier modules if overwritten by information in later modules.
        """
        import copy
        cdict = dict()
        for name in module_names:
            mdict = TissueModel._createDict(name)
            for key, value in mdict.iteritems():
                if type(value) is list:
                    # create new list
                    if not cdict.has_key(key):
                        cdict[key] = []
                    # now add the elements by copy
                    cdict[key].extend(copy.deepcopy(value))

                elif type(value) is dict:
                    # create new dict
                    if not cdict.has_key(key):
                        cdict[key] = dict()
                    # now add the elements by copy
                    old_value = cdict.get(key)
                    for k, v in value.iteritems():
                        old_value[k] = copy.deepcopy(v)
        return cdict

    @staticmethod
    def _createDict(module_name):
        """
        A module which encodes a cell model is given and
        used to create the instance of the CellModel from
        the given global variables of the module.

        TODO: some quality control of the model structure.
        """
        # dynamically import module
        # tissue_module = __import__(module_name)
        import importlib
        module = importlib.import_module(module_name)

        # get attributes from the class
        print '\n***', module_name, '***'
        print module
        print dir(module)

        mdict = dict()
        for key in TissueModel._keys:
            if hasattr(module, key):
                # print 'set:', key
                mdict[key] = getattr(module, key)
            else:
                print 'missing:', key

        return mdict

    def createId(self):
        if self.simId:
            mid = '{}_v{}_Nc{}_{}'.format(self.cellModel.mid, self.version, self.Nc, self.simId)
        else:
            mid = '{}_v{}_Nc{}'.format(self.cellModel.mid, self.version, self.Nc)
        return mid

    def cell_range(self):
        return range(1, self.Nc + 1)

    def comp_range(self):
        return range(1, self.Nc * self.Nf + 1)

    def info(self):
        for key in TissueModel._keys:
            print key, ' : ', getattr(self, key)

    def createModel(self):
        # sinusoidal unit model
        self.createUnits()
        self.createExternalParameters()
        self.createInitialAssignments()
        self.createExternalCompartments()
        self.createExternalSpecies()
        self.createAssignmentRules()
        self.createTransportReactions()
        self.createBoundaryConditions()
        # cell model
        self.createCellCompartments()
        self.createCellSpecies()
        self.createCellParameters()
        self.createCellInitialAssignments()
        self.createCellAssignmentRules()
        self.createCellReactions()
        # events
        self.createCellEvents()
        self.createSimulationEvents()

    #########################################################################
    # External Compartments
    ##########################################################################
    # id, name, spatialDimension, unit, constant, assignment/value
    def createExternalCompartmentsDict(self):
        comps = dict()
        # periportal
        comps[getPPId()] = (getPPName(), 3, 'm3', False, 'Vol_pp')
        # sinusoid
        for k in self.comp_range():
            comps[getSinusoidId(k)] = (getSinusoidName(k), 3, 'm3', False, 'Vol_sin')
        # disse
        for k in self.comp_range():
            comps[getDisseId(k)] = (getDisseName(k), 3, 'm3', False, 'Vol_dis')
        # perivenious
        comps[getPVId()] = (getPVName(), 3, 'm3', False, 'Vol_pv')
        return comps

    ##########################################################################
    # Cell compartments
    ##########################################################################
    def createCellCompartmentsDict(self):
        comps = dict()
        # hepatocyte compartments
        for k in self.cell_range():
            comps[getHepatocyteId(k)] = (getHepatocyteName(k), 3, 'm3', False, 'Vol_cell')
            comps[getCytosolId(k)] = (getCytosolName(k), 3, 'm3', False, 'Vol_cyto')
        return comps

    ##########################################################################
    # Species
    ##########################################################################
    def createExternalSpeciesDict(self):
        """
        All species which are defined external are generated in all
        external compartments, i.e. PP, PV, sinusoid and disse space.
        """
        sdict = dict()
        for data in self.external:
            (sid, init, units, boundaryCondition) = self.getItemsFromSpeciesData(data)
            name = self.names[sid]
            # PP
            sdict[getPPSpeciesId(sid)] = (getPPSpeciesName(name), init, units, getPPId(), boundaryCondition)
            for k in self.comp_range():
                sdict[getSinusoidSpeciesId(sid, k)] = (
                    getSinusoidSpeciesName(name, k), init, units, getSinusoidId(k), boundaryCondition)
                sdict[getDisseSpeciesId(sid, k)] = (
                    getDisseSpeciesName(name, k), init, units, getDisseId(k), boundaryCondition)
            # PV
            sdict[getPVSpeciesId(sid)] = (getPVSpeciesName(name), init, units, getPVId(), boundaryCondition)
        return sdict

    def createCellSpeciesDict(self):
        sdict = dict()
        for data in self.cellModel.species:
            (full_id, init, units, boundaryCondition) = self.getItemsFromSpeciesData(data)

            tokens = full_id.split('__')
            sid = tokens[1]
            name = self.names[sid]
            for k in self.cell_range():
                # TODO: only covers species in cytosol (has to work with arbitrary number of compartments)
                # necessary to have a mapping of the compartments to the functions which generate id and names
                if full_id.startswith('h__'):
                    sdict[getHepatocyteSpeciesId(sid, k)] = (getHepatocyteSpeciesName(name, k), init, units,
                                                             getHepatocyteId(k), boundaryCondition)
                if full_id.startswith('c__'):
                    sdict[getCytosolSpeciesId(sid, k)] = (getCytosolSpeciesName(name, k), init, units,
                                                          getCytosolId(k), boundaryCondition)
        return sdict

    def getItemsFromSpeciesData(self, data):
        sid, init, units = data[0], data[1], data[2]
        # handle the constant species
        if len(data) == 4:
            boundaryCondition = data[3]
        else:
            boundaryCondition = False
        return sid, init, units, boundaryCondition

    ##########################################################################
    # Diffusion
    ##########################################################################
    def createDiffusionAssignments(self):
        """ Create the geometrical diffusion constants
            based on the external substances.
            For the diffusion between sinusoid and space of Disse,
            diffusion through fenestrations is handled via pore theory.
        """
        # get the fenestration radius
        r_fen = None
        for p in self.pars:
            if p[0] == 'r_fen':
                r_fen = p[1]
                break
        if not r_fen:
            raise TissueModelException('Fenestration radius not defined.')

        diffusion_assignments = []
        for data in self.external:
            sid = data[0]
            # id, assignment, unit
            diffusion_assignments.extend([
                ('Dx_sin_{}'.format(sid), 'D{}/x_sin * A_sin'.format(sid), "m3_per_s"),
                ('Dx_dis_{}'.format(sid), 'D{}/x_sin * A_dis'.format(sid), "m3_per_s"),
                # ('Dy_sindis_{}'.format(sid), 'D{}/y_dis * f_fen * A_sindis'.format(sid), "m3_per_s")
                # check the pore size
            ])
            # test if substance larger than fenestration radius
            r_sid = None
            for p in self.pars:
                if p[0] == 'r_{}'.format(sid):
                    r_sid = p[1]
                    break
            if r_sid > r_fen:
                diffusion_assignments.extend([('Dy_sindis_{}'.format(sid), '0 m3_per_s', "m3_per_s")])
            else:
                diffusion_assignments.extend([('Dy_sindis_{}'.format(sid),
                                               'D{}/y_dis * f_fen * A_sindis * (1 dimensionless - r_{}/r_fen)^2 * (1 dimensionless - 2.104 dimensionless*r_{}/r_fen + 2.09 dimensionless *(r_{}/r_fen)^3 - 0.95 dimensionless *(r_{}/r_fen)^5)'.format(
                                                   sid, sid, sid, sid, sid),
                                               "m3_per_s")])
        return diffusion_assignments

    def createDiffusionRules(self):
        return self.createDiffusionAssignments()

    # Parameters
    def createParametersDict(self, pars):
        pdict = dict()
        for pdata in pars:
            pid = pdata[0]
            # id, name, value, unit, constant
            pdict[pid] = [pid, self.names.get(pid, None),
                          pdata[1], pdata[2], pdata[3]]
        return pdict

    # Units
    def createUnits(self):
        # creates all the individual unit definitions
        for key, value in self.units.iteritems():
            createUnitDefinition(self.model, key, value)
        # sets the main units of model
        setMainUnits(self.model, self.main_units)

    # Compartments
    def createExternalCompartments(self):
        comps = self.createExternalCompartmentsDict()
        createCompartments(self.model, comps)

    def createCellCompartments(self):
        comps = self.createCellCompartmentsDict()
        createCompartments(self.model, comps)

    # Species
    def createExternalSpecies(self):
        species = self.createExternalSpeciesDict()
        createSpecies(self.model, species)

    def createCellSpecies(self):
        species = self.createCellSpeciesDict()
        createSpecies(self.model, species)

    # Parameters
    def createExternalParameters(self):
        parameters = self.createParametersDict(self.pars)
        createParameters(self.model, parameters)

    def createCellParameters(self):
        parameters = self.createParametersDict(self.cellModel.pars)
        createParameters(self.model, parameters)

    # InitialAssignments
    def createInitialAssignments(self):
        createInitialAssignments(self.model, self.assignments, self.names)
        # diffusion
        # dif_assignments = self.createDiffusionAssignments()
        # createInitialAssignments(self.model, dif_assignments, self.names)

    def createCellInitialAssignments(self):
        createInitialAssignments(self.model, self.cellModel.assignments, self.names)

    # Assignment Rules
    def createAssignmentRules(self):
        createAssignmentRules(self.model, self.rules, self.names)

        # diffusion
        dif_rules = self.createDiffusionRules()
        createAssignmentRules(self.model, dif_rules, self.names)

    def createCellAssignmentRules(self):
        rules = []
        rep_dicts = self.createCellExtReplacementDicts()
        for rule in self.cellModel.rules:
            for d in rep_dicts:
                r_new = [initString(rpart, d) for rpart in rule]
                rules.append(r_new)
        createAssignmentRules(self.model, rules, self.names)

    def createCellReplacementDicts(self):
        """ Definition of replacement information for initialization of the cell ids.
            Creates all possible combinations.
        """
        init_data = []
        for k in self.cell_range():
            d = dict()
            d['h__'] = '{}__'.format(getHepatocyteId(k))
            d['c__'] = '{}__'.format(getCytosolId(k))
            init_data.append(d)
        return init_data

    def createCellExtReplacementDicts(self):
        """ Definition of replacement information for initialization of the cell ids.
            Creates all possible combinations.
        """
        init_data = []
        for k in self.cell_range():
            for i in range((k - 1) * self.Nf + 1, k * self.Nf + 1):
                d = dict()
                d['h__'] = '{}__'.format(getHepatocyteId(k))
                d['c__'] = '{}__'.format(getCytosolId(k))
                d['e__'] = '{}__'.format(getDisseId(i))
                init_data.append(d)
        return init_data

    # Boundary Conditions
    def createBoundaryConditions(self):
        ''' Set constant in periportal. '''
        sdict = self.createExternalSpeciesDict()
        for key in sdict.keys():
            if isPPSpeciesId(key):
                s = self.model.getSpecies(key)
                s.setBoundaryCondition(True)

    # Reactions
    def createCellReactions(self):
        """ Initializes the generic compartments with the actual
            list of compartments for the given geometry.
        """
        # set the model for the template
        reaction.model = self.model

        rep_dicts = self.createCellReplacementDicts()
        for r in self.cellModel.reactions:
            # Get the right replacement dictionaries for the reactions
            if ('c__' in r.compartments) and not ('e__' in r.compartments):
                rep_dicts = self.createCellReplacementDicts()
            if ('c__' in r.compartments) and ('e__' in r.compartments):
                rep_dicts = self.createCellExtReplacementDicts()
            r.createReactions(self.model, rep_dicts)

    def createTransportReactions(self):
        self.createFlowRules()
        self.createFlowReactions()
        self.createFlowPoreReactions()
        self.createDiffusionReactions()

    def createFlowRules(self):
        """ Creates the rules for positions Si_x, pressures Si_P,
            capillary flow Si_Q and pore flow Si_q.
            These parameters are used afterwards to calculate the actual flow
            values.
        """
        rules = [
            (getPositionId(getPPId()), '0 m', 'm'),
            (getPositionId(getPVId()), 'L', 'm'),
        ]
        # position midpoint hepatocyte
        for k in range(1, self.Nc * self.Nf + 1):
            r = (getPositionId(getSinusoidId(k)), '({} dimensionless-0.5 dimensionless)*x_sin'.format(k), 'm')
            rules.append(r)
        # position in between hepatocytes
        for k in range(1, self.Nc * self.Nf):
            r = (getPositionId(getSinusoidId(k), getSinusoidId(k + 1)), '{} dimensionless*x_sin'.format(k), 'm')
            rules.append(r)

        # pressures
        P_formula = '(-(Pb-P0) + (Pa-P0)*exp(-L/lambda))/(exp(-L/lambda)-exp(L/lambda))*exp( {}/lambda)\
                 + ( (Pb-P0) - (Pa-P0)*exp( L/lambda))/(exp(-L/lambda)-exp(L/lambda))*exp(-{}/lambda) + P0'
        # PP, PV
        for vid in [getPPId(), getPVId()]:
            x_str = getPositionId(vid)
            P_str = getPressureId(vid)
            rules.append((P_str, P_formula.format(x_str, x_str), 'Pa'))
        # midpoint
        for k in self.comp_range():
            x_str = getPositionId(getSinusoidId(k))
            P_str = getPressureId(getSinusoidId(k))
            rules.append((P_str, P_formula.format(x_str, x_str), 'Pa'))

        # capillary flow
        Q_formula = '-1 dimensionless/sqrt(W*w) * ( (-(Pb-P0) + (Pa-P0)*exp(-L/lambda))/(exp(-L/lambda)-exp(L/lambda))*exp( {}/lambda)\
        - ( (Pb-P0) - (Pa-P0)*exp( L/lambda))/(exp(-L/lambda)-exp(L/lambda))*exp(-{}/lambda) )'
        # PP, PV
        for vid in [getPPId(), getPVId()]:
            x_str = getPositionId(vid)
            Q_str = getQFlowId(vid)
            rules.append((Q_str, Q_formula.format(x_str, x_str), 'm3_per_s'))
        # between locations
        for k in range(1, self.Nc * self.Nf):
            x_str = '{}{}_x'.format(getSinusoidId(k), getSinusoidId(k + 1))
            Q_str = '{}{}_Q'.format(getSinusoidId(k), getSinusoidId(k + 1))
            rules.append((Q_str, Q_formula.format(x_str, x_str), 'm3_per_s'))

        # pore flow (only along sinusoid, not in PP and PV)
        q_formula = '1 dimensionless/w  * ( (-(Pb-P0) + (Pa-P0)*exp(-L/lambda))/(exp(-L/lambda)-exp(L/lambda))*exp( {}/lambda) \
        + ( (Pb-P0) - (Pa-P0)*exp( L/lambda))/(exp(-L/lambda)-exp(L/lambda))*exp(-{}/lambda) )'

        # midpoint
        for k in self.comp_range():
            x_str = '{}_x'.format(getSinusoidId(k))
            q_str = '{}_q'.format(getSinusoidId(k))
            rules.append((q_str, q_formula.format(x_str, x_str), 'm2_per_s'))

        createAssignmentRules(self.model, rules, {})

    def createFlowReactions(self):
        """
        Creates the local flow reactions based on the local volume flows.
        The amount of substance transported via the volume flow is calculated.
        """
        # flow = 'flow_sin * A_sin'     # [m3/s] global volume flow (converts to local volume flow in pressure model)
        for data in self.external:
            sid = data[0]
            # flow PP -> S01
            Q_str = getQFlowId(getPPId())  # [m3/s] local volume flow
            createFlowReaction(self.model, sid, c_from=getPPId(), c_to=getSinusoidId(1),
                               flow=Q_str)  # [m3/s] local volume flow
            # flow S[k] -> S[k+1]
            for k in range(1, self.Nc * self.Nf):
                Q_str = getQFlowId(getSinusoidId(k), getSinusoidId(k + 1))
                createFlowReaction(self.model, sid, c_from=getSinusoidId(k), c_to=getSinusoidId(k + 1), flow=Q_str)
            # flow S[Nc*Nf] -> PV
            Q_str = getQFlowId(getPVId())
            createFlowReaction(self.model, sid, c_from=getSinusoidId(self.Nc * self.Nf), c_to=getPVId(), flow=Q_str)
            # flow PV ->
            createFlowReaction(self.model, sid, c_from=getPVId(), c_to=NONE_ID, flow=Q_str);

    def createFlowPoreReactions(self):
        """ Filtration and reabsorption reactions through pores. """
        for data in self.external:
            sid = data[0]
            if sid in ["rbcM"]:
                continue  # only create for substances fitting through pores

            # flow S[k] -> D[k]
            for k in self.comp_range():
                Q_str = getqFlowId(getSinusoidId(k)) + ' * {}'.format('x_sin')  # [m2/s] * [m] (area flow)
                createFlowReaction(self.model, sid, c_from=getSinusoidId(k), c_to=getDisseId(k), flow=Q_str)

    def createDiffusionReactions(self):
        for data in self.external:
            sid = data[0]
            # [1] sinusoid diffusion
            Dx_sin = 'Dx_sin_{}'.format(sid)
            createDiffusionReaction(self.model, sid, c_from=getPPId(), c_to=getSinusoidId(1), D=Dx_sin)

            for k in range(1, self.Nc * self.Nf):
                createDiffusionReaction(self.model, sid, c_from=getSinusoidId(k), c_to=getSinusoidId(k + 1), D=Dx_sin)
            createDiffusionReaction(self.model, sid, c_from=getSinusoidId(self.Nc * self.Nf), c_to=getPVId(), D=Dx_sin)

            # [2] disse diffusion
            Dx_dis = 'Dx_dis_{}'.format(sid)
            for k in range(1, self.Nc * self.Nf):
                createDiffusionReaction(self.model, sid, c_from=getDisseId(k), c_to=getDisseId(k + 1), D=Dx_dis)

            # [3] sinusoid - disse diffusion
            Dy_sindis = 'Dy_sindis_{}'.format(sid)
            for k in self.comp_range():
                createDiffusionReaction(self.model, sid, c_from=getSinusoidId(k), c_to=getDisseId(k), D=Dy_sindis)

    # Events
    def createCellEvents(self):
        """ Creates the additional events defined in the cell model.
            These can be metabolic deficiencies, or other defined
            parameter changes.
            TODO: make this cleaner and more general.
        """

        ddict = self.cellModel.deficiencies
        dunits = self.cellModel.deficiencies_units

        for deficiency, data in ddict.iteritems():
            e = createDeficiencyEvent(self.model, deficiency)
            # create all the event assignments for the event
            for key, value in data.iteritems():
                p = self.model.getParameter(key)
                p.setConstant(False)
                formula = '{} {}'.format(value, dunits[key])
                astnode = libsbml.parseL3FormulaWithModel(formula, self.model)
                ea = e.createEventAssignment()
                ea.setVariable(key)
                ea.setMath(astnode)

    def createSimulationEvents(self):
        """ Create the simulation timecourse events based on the
            event data.
        """
        if self.events:
            createSimulationEvents(self.model, self.events)

    def writeSBML(self, filepath=None, validate=True):
        if not filepath:
            filepath = self.sbml_default_path()

        print 'Write : {}\n'.format(self.id, filepath)
        writer = SBMLWriter()
        writer.writeSBMLToFile(self.doc, filepath)

        # validate the model with units (only for small models)
        if validate:
            validator = SBMLValidator(ucheck=(self.Nc < 4))
            validator.validate(filepath)
        return filepath

    def sbml_default_path(self):
        import os
        from multiscale import multiscale_settings

        return os.path.join(multiscale_settings.SBML_DIR, '{}.xml'.format(self.id))
