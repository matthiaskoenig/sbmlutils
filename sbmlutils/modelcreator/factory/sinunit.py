"""
Sinusoidal tissue factory.

Creates a sinusoidal tissue model from given information
of the structure (number of cells/compartments) and the properties of the
transported substances.
"""

from libsbml import SBMLDocument, SBMLWriter

from sbmlutils.modelcreator.processes import *
from sbmlutils.modelcreator.processes import ReactionTemplate
from sbmlutils.modelcreator.modelcreator import CoreModel
from sbmlutils.factory import Species, Compartment

from sinnaming import *


class SinusoidSpecies(object):
    """ Species/Substance transported in the sinusoidal unit. """
    def __init__(self, sid, value, unit, D, r, name=None):
        self.sid = sid
        self.value = value
        self.unit = unit
        self.D = D
        self.r = r
        self.name = name


class SinusoidalUnitFactory(object):
    """
    Creates the necessary information to create
    a model.

    The file creates an intermediary model object from which
    in a subsequent step the SBML is created.
    """
    def __init__(self, Nc, sin_species, core_model):

        self.Nc = Nc
        self.sin_species = sin_species
        self.mid = 'SinusoidalUnit_Nc{}'.format(self.Nc)
        self.core_model = core_model

        # extend the core model with sinusoidal unit information
        self.create_sinusoid_model()

    def cell_range(self):
        """ Helper to iterate over the cells & respective compartments. """
        return range(1, self.Nc+1)

    def create_sinusoid_model(self):
        """ Dynamic creation of the core model.

        :return:
        :rtype:
        """

        # sinusoidal unit model
        # self.createUnits()
        # self.createExternalParameters()
        # self.createInitialAssignments()

        self.core_model.compartments.extend(self.createCompartments())
        self.core_model.species.extend(self.createSpecies())

        # self.createAssignmentRules()
        # self.createTransportReactions()
        # self.createBoundaryConditions()

    #########################################################################
    # Compartments
    ##########################################################################
    def createCompartments(self):
        """ Creates the compartments of the sinusoidal architecture.
        :return:
        :rtype:
        """

        # periportal and perivenous
        compartments = [
            Compartment(getPPId(), 'Vol_pp', 'm3', constant=False, name=getPPName()),
            Compartment(getPVId(), 'Vol_pv', 'm3', constant=False, name=getPVName())
        ]
        # sinusoid, disse and hepatocyte compartments
        for k in self.cell_range():
            compartments.extend([
                Compartment(getSinusoidId(k), 'Vol_sin', 'm3', constant=False, name=getSinusoidName(k)),
                Compartment(getDisseId(k), 'Vol_dis', 'm3', constant=False, name=getDisseName(k)),
                Compartment(getHepatocyteId(k), 'Vol_cell', 'm3', constant=False, name=getHepatocyteName(k)),
            ])

        return compartments

    ##########################################################################
    # Species
    ##########################################################################
    def createSpecies(self):
        """
        All species which are defined external are generated in all
        external compartments, i.e. PP, PV, sinusoid and disse space.
        """
        species = []
        for s in self.sin_species:
            sid = s.sid
            name = s.name
            # PP & PV
            species.extend([
                Species(getPPSpeciesId(sid), s.value, compartment=getPPId(), unit=s.unit,
                        boundaryCondition=True, name=getPPSpeciesName(name)),
                Species(getPVSpeciesId(sid), s.value, compartment=getPVId(), unit=s.unit,
                        boundaryCondition=False, name=getPVSpeciesName(name))
            ])
            # sinusoid & disse space
            for k in self.cell_range():
                species.extend([
                    Species(getSinusoidSpeciesId(sid, k), s.value, compartment=getSinusoidId(k), unit=s.unit,
                            boundaryCondition=False, name=getSinusoidSpeciesName(name, k)),
                    Species(getDisseSpeciesId(sid, k), s.value, compartment=getDisseId(k), unit=s.unit,
                            boundaryCondition=False, name=getDisseSpeciesName(name, k))
                ])
        return species

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
                                               'D{}/y_dis * f_fen * A_sindis * (1 dimensionless - r_{}/r_fen)^2 * (1 dimensionless - 2.104 dimensionless*r_{}/r_fen + 2.09 dimensionless *(r_{}/r_fen)^3 - 0.95 dimensionless *(r_{}/r_fen)^5)'.format(sid, sid, sid, sid, sid),
                                               "m3_per_s")])
        return diffusion_assignments

    def createDiffusionRules(self):
        return self.createDiffusionAssignments()

 
    # InitialAssignments
    def createInitialAssignments(self):
        createInitialAssignments(self.model, self.assignments, self.names)
        # diffusion
        # dif_assignments = self.createDiffusionAssignments()
        # createInitialAssignments(self.model, dif_assignments, self.names)


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
    


    # Boundary Conditions
    def createBoundaryConditions(self):
        """ Set constant in periportal.

        """
        # TODO: handle this in the species creation
        sdict = self.createExternalSpeciesDict()
        for key in sdict.keys():
            if isPPSpeciesId(key):
                s = self.model.getSpecies(key)
                s.setBoundaryCondition(True)


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
        for k in range(1, self.Nc*self.Nf+1):
            r = (getPositionId(getSinusoidId(k)), '({} dimensionless-0.5 dimensionless)*x_sin'.format(k), 'm')
            rules.append(r)
        # position in between hepatocytes
        for k in range(1, self.Nc*self.Nf):
            r = (getPositionId(getSinusoidId(k), getSinusoidId(k+1)), '{} dimensionless*x_sin'.format(k), 'm')
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
        for k in range(1, self.Nc*self.Nf):
            x_str = '{}{}_x'.format(getSinusoidId(k), getSinusoidId(k+1))
            Q_str = '{}{}_Q'.format(getSinusoidId(k), getSinusoidId(k+1))
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
            Q_str = getQFlowId(getPPId()) # [m3/s] local volume flow
            createFlowReaction(self.model, sid, c_from=getPPId(), c_to=getSinusoidId(1), flow=Q_str) # [m3/s] local volume flow
            # flow S[k] -> S[k+1] 
            for k in range(1, self.Nc*self.Nf):
                Q_str = getQFlowId(getSinusoidId(k), getSinusoidId(k+1))
                createFlowReaction(self.model, sid, c_from=getSinusoidId(k), c_to=getSinusoidId(k+1), flow=Q_str)
            # flow S[Nc*Nf] -> PV
            Q_str = getQFlowId(getPVId())
            createFlowReaction(self.model, sid, c_from=getSinusoidId(self.Nc*self.Nf), c_to=getPVId(), flow=Q_str)
            # flow PV ->
            createFlowReaction(self.model, sid, c_from=getPVId(), c_to=NONE_ID, flow=Q_str);
    
    def createFlowPoreReactions(self):
        """ Filtration and reabsorption reactions through pores. """
        for data in self.external:
            sid = data[0]      
            if sid in ["rbcM"]: 
                continue   # only create for substances fitting through pores
            
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
            
            for k in range(1, self.Nc*self.Nf):
                createDiffusionReaction(self.model, sid, c_from=getSinusoidId(k), c_to=getSinusoidId(k+1), D=Dx_sin)
            createDiffusionReaction(self.model, sid, c_from=getSinusoidId(self.Nc*self.Nf), c_to=getPVId(), D=Dx_sin)
            
            # [2] disse diffusion
            Dx_dis = 'Dx_dis_{}'.format(sid)
            for k in range(1, self.Nc*self.Nf):
                createDiffusionReaction(self.model, sid, c_from=getDisseId(k), c_to=getDisseId(k+1), D=Dx_dis)
            
            # [3] sinusoid - disse diffusion
            Dy_sindis = 'Dy_sindis_{}'.format(sid)
            for k in self.comp_range():
                createDiffusionReaction(self.model, sid, c_from=getSinusoidId(k), c_to=getDisseId(k), D=Dy_sindis)

