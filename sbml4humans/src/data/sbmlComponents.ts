/* SBML Component Representations */

const CVTerm = {
    url: String,
    resources: [String],
};

const History = {
    creators: [
        {
            givenName: String,
            familyName: String,
            organization: String,
            email: String,
        },
    ],
    createdDate: String,
    modifiedDates: [String],
};

const UncertaintyParameter = {
    var: String,
    value: Number,
    units: String,
    type: String,
    definitionURL: String,
    math: String,
};

const Uncertainty = {
    pk: String,
    id: String,
    metaId: String,
    name: String,
    sbo: String,
    cvTerms: [CVTerm],
    history: History,
    notes: String,
    xml: String,
    sbmlType: String,
    uncertaintyParameters: [UncertaintyParameter],
};

/**
 * SBase: The parent class of (almost) all SBML objects
 */
const SBase = {
    pk: String,
    id: String,
    metaId: String,
    name: String,
    sbo: String,
    cvTerms: [CVTerm],
    history: History,
    notes: String,
    xml: String,
    sbmlType: String,

    // comp
    replacedBy: {
        submodelRef: String,
        replacedBySbaseref: String,
    },
    replacedElements: {
        submodelRef: String,
        replacedElementSbaseref: String,
    },

    // distrib
    uncertainties: [Uncertainty],
};

const sbaseRef = {
    ...SBase,
    portRef: String,
    idRef: String,
    unitRef: String,
    metaIdRef: String,
    referencedElement: {
        element: String,
        elementId: String,
    },
};

const Assignment = {
    pk: String,
    sbmlType: String,
};

/**
 * SBML Document definition from which the report is to be generated
 */
const SBMLDocument = {
    ...SBase,
    packages: {
        document: {
            level: Number,
            version: Number,
        },
        plugins: [
            {
                prefix: String,
                version: Number,
            },
        ],
    },
};

const ModelBase = {
    ...SBase,
    substanceUnits: String,
    timeUnits: String,
    volumeUnits: String,
    areaUnits: String,
    lengthUnits: String,
    extentUnits: String,
    conversionFactor: String,
};

const FunctionDefinition = {
    ...SBase,
    math: String,
};

const UnitDefinition = {
    ...SBase,
    units: String,
};

const Compartment = {
    sbase: SBase,
    spatialDimensions: Number,
    size: Number,
    constant: Boolean,
    units: String,
    derivedUnits: String,
    assignment: Assignment,

    // cross links
    species: [String], // list of pks of related species
    reactions: [String], // list of pks of related reactions
};

const Species = {
    ...SBase,
    compartment: String,
    initialAmount: Number,
    initialConcentration: Number,
    substanceUnits: String,
    hasOnlySubstanceUnits: Boolean,
    boundaryCondition: Boolean,
    constant: Boolean,
    units: String,
    derivedUnits: String,
    assignment: Assignment,
    conversionFactor: {
        sid: String,
        value: Number,
        units: String,
    },
    fbc: {
        formula: String,
        charge: Number,
    },

    // cross links
    reactant: [String],
    product: [String],
    modifier: [String],
};

const Parameter = {
    ...SBase,
    value: Number,
    constant: Boolean,
    units: String,
    derivedUnits: String,
    assignment: Assignment,
};

const InitialAssignment = {
    ...SBase,
    symbol: String,
    math: String,
    derivedUnits: String,
};

// Rule [parent for AssignmentRule, RateRule and AlgebraicRule]
const Rule = {
    ...SBase,
    variable: String,
    math: String,
    derivedUnits: String,
};

const AssignmentRule = Rule;
const RateRule = Rule;
const AlgebraicRule = Rule;

const Constraint = {
    ...SBase,
    math: String,
    message: String,
};

const Reaction = {
    ...SBase,
    reversible: Boolean,
    compartment: String,
    listOfReactants: [
        {
            species: String,
            stoichiometry: Number,
            constant: Boolean,
        },
    ],
    listOfProducts: [
        {
            species: String,
            stoichiometry: Number,
            constant: Boolean,
        },
    ],
    listOfModifiers: [String],
    fast: Boolean,
    equation: String,
    kineticLaw: {
        math: String,
        derivedUnits: String,
        listOfLocalParameters: [
            {
                id: String,
                value: Number,
                units: String,
                derivedUnits: String,
            },
        ],
    },
    fbc: {
        bounds: {
            lowerFluxBound: {
                id: String,
                value: Number,
            },
            upperFluxBound: {
                id: String,
                value: Number,
            },
        },
        gpa: String,
    },
};

const Event = {
    ...SBase,
    useValuesFromTriggerTime: Boolean,
    trigger: {
        math: String,
        initialValue: Number,
        persistent: Boolean,
    },
    priority: String,
    delay: String,
    listOfEventAssignments: [
        {
            variable: String,
            math: String,
        },
    ],
};

/**
 * FBC components
 */

const GeneProduct = {
    ...SBase,
    label: String,
    associatedSpecies: String,
};

const Objective = {
    ...SBase,
    type: String,
    fluxObjectives: [
        {
            sign: String,
            coefficient: Number,
            reaction: String,
        },
    ],
};

/**
 * Comp Components
 */

const Submodel = {
    ...SBase,
    modelRef: String,
    deletions: [
        {
            type: String,
            value: String,
        },
    ],
    timeConversion: String,
    extentConversion: String,
};

const Port = {
    ...sbaseRef,
};

/**
 * Definition of SBML Model
 */
const Model = {
    // model's own attributes
    ...ModelBase,

    // core
    functionDefinitions: [FunctionDefinition],
    unitDefinitions: [UnitDefinition],
    compartments: [Compartment],
    species: [Species],
    parameters: [Parameter],
    initialAssignments: [InitialAssignment],
    assignmentRules: [AssignmentRule],
    rateRules: [RateRule],
    algebraicRules: [AlgebraicRule],
    constraints: [Constraint],
    reactions: [Reaction],
    events: [Event],

    // comp
    submodels: [Submodel],
    ports: [Port],

    // fbc
    geneProducts: [GeneProduct],
    objectives: [Objective],
};

const ModelDefinition = {
    ...Model,
};

const ExternalModelDefinition = {
    ...SBase,
    modelRef: String,
    source: String,
};

/**
 * Definitions of commonly used data structures
 */
const Report = {
    doc: SBMLDocument,
    model: Model,
    modelDefinitions: [ModelDefinition],
    externalModelDefinitions: [ExternalModelDefinition],
};

const DetailInfo = { ...SBase, ...Reaction, ...Rule };

const RawData = {
    report: Report,
    debug: {
        jsonReportTime: String,
    },
};

export default {
    SBase: SBase,
    SBMLDocument: SBMLDocument,
    Model: Model,
    FunctionDefinition: FunctionDefinition,
    UnitDefinition: UnitDefinition,
    Compartment: Compartment,
    Species: Species,
    Parameter: Parameter,
    InitialAssignment: InitialAssignment,
    AssignmentRule: AssignmentRule,
    RateRule: RateRule,
    AlgebraicRule: AlgebraicRule,
    Constraint: Constraint,
    Reaction: Reaction,
    Event: Event,
    Submodel: Submodel,
    Port: Port,
    GeneProduct: GeneProduct,
    Objective: Objective,
    Report: Report,
    RawData: RawData,
    DetailInfo: DetailInfo,
};
