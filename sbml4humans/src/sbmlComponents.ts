/* SBML Component Model Representations */

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

const mathDict = {
    type: String,
    math: String,
};

// sbase
const SBase = {
    id: String,
    metaId: String,
    name: String,
    sbo: String,
    cvTerms: [CVTerm],
    history: [History],
    notes: String,
    xml: String,
    displaySId: String,
    sbmlType: String,
    pk: String,
};

// doc
const SBMLDocument = {
    sbase: SBase,
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

// model
const Model = {
    sbase: SBase,
    substanceUnits: String,
    timeUnits: String,
    volumeUnits: String,
    areaUnits: String,
    lengthUnits: String,
    extentUnits: String,
    conversionFactor: String,
};

// function definition
const FunctionDefinition = {
    sbase: SBase,
    math: mathDict,
};

// unit definition
const UnitDefinition = {
    sbase: SBase,
    listOfUnits: [
        {
            nomTerms: [
                {
                    scale: Number,
                    multiplier: Number,
                    exponent: Number,
                    kind: {
                        name: String,
                    },
                },
            ],
            denomTerms: [
                {
                    scale: Number,
                    multiplier: Number,
                    exponent: Number,
                    kind: String,
                },
            ],
        },
    ],
};

const derivedUnits = {
    math: String,
    unitTerms: [
        {
            scale: Number,
            multiplier: Number,
            exponent: Number,
            kind: String,
        },
    ],
};

// compartment
const Compartment = {
    sbase: SBase,
    spatialDimensions: Number,
    size: Number,
    units: UnitDefinition, // add unit
    constant: Boolean,
};

const Species = {
    sbase: SBase,
    compartment: Compartment,
    initialAmount: Number,
    initialConcentration: Number,
    substanceUnits: String,
    hasOnlySubstanceUnits: Boolean,
    boundaryCondition: Boolean,
    constant: Boolean,
    conversionFactor: {
        sid: String,
        value: Number,
        units: String,
    },
    fbc: {
        formula: String,
        charge: Number,
    },
};

const Parameter = {
    sbase: SBase,
    value: Number,
    units: derivedUnits,
    constant: Boolean,
};

const InitialAssignment = {
    sbase: SBase,
    symbol: String,
    math: mathDict,
    units: derivedUnits,
};

const Rule = {
    sbase: SBase,
    variable: String,
    math: mathDict,
    units: derivedUnits,
};

const Constraint = {
    sbase: SBase,
    math: mathDict,
    message: String,
};

const Reaction = {
    sbase: SBase,
    reversible: Boolean,
    compartment: Compartment,
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
        math: mathDict,
        units: derivedUnits,
        listOfLocalParameters: [
            {
                id: String,
                value: Number,
                units: derivedUnits,
            },
        ],
    },
};

const Objective = {
    sbase: SBase,
    type: String,
    fluxObjectives: [
        {
            sign: String,
            coefficient: Number,
            reaction: Reaction,
        },
    ],
};

const Event = {
    sbase: SBase,
    useValuesFromTriggerTime: Boolean,
    trigger: {
        math: mathDict,
        initialValue: Number,
        persistent: Boolean,
    },
    priority: mathDict,
    delay: mathDict,
    listOfEventAssignments: [
        {
            variable: String,
            math: mathDict,
        },
    ],
};

const GeneProduct = {
    sbase: SBase,
    label: String,
    associatedSpecies: Species,
};

const sbaseRef = {
    sbase: SBase,
    portRef: String,
    idRef: String,
    unitRef: String,
    metaIdRef: String,
    referencedElement: {
        element: String,
        elementId: String,
    },
};

const SubModel = {
    sbase: SBase,
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
    sbaseRef: sbaseRef,
};

const Models = {
    model: Model,
    submodels: [SubModel],
    ports: [Port],
    functionDefinitions: [FunctionDefinition],
    unitDefinitions: [UnitDefinition],
    compartments: [Compartment],
    species: [Species],
    parameters: [Parameter],
    initialAssignments: [InitialAssignment],
    rules: [Rule],
    constraints: [Constraint],
    reactions: [Reaction],
    objectives: [Objective],
    events: [Event],
    geneProducts: [GeneProduct],
};

const ModelDefinitions = {
    modelDefs: [],
    externalModelDefs: [
        {
            sbase: SBase,
            replaced_by: {
                class: String,
                source_code: String,
            },
            replaced_elements: [
                {
                    submodelRef: String,
                    replacedBySbaseref: {
                        class: String,
                        source_code: String,
                    },
                },
            ],
            type: {
                class: String,
                source_code: String,
            },
        },
    ],
}; // refactor

const Report = {
    doc: SBMLDocument,
    modelDefinitions: ModelDefinitions,
    models: Models,
};

const DetailInfo = SBase;

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
    Rule: Rule,
    Constraint: Constraint,
    Reaction: Reaction,
    Objective: Objective,
    Event: Event,
    GeneProduct: GeneProduct,
    SubModel: SubModel,
    Port: Port,
    Models: Models,
    ModelDefinitions: ModelDefinitions,
    Report: Report,
    RawData: RawData,
    DetailInfo: DetailInfo,
};
