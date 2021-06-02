/* SBML Component Model Representations */

type CVTerm = {
    url: string;
    resources: string[];
};

type History = {
    creators: {
        givenName: string;
        familyName: string;
        organization: string;
        email: string;
    }[];
    createdDate: string;
    modifiedDates: string[];
};

type mathDict = {
    type: string;
    math: string;
};

// sbase
type SBase = {
    id: string;
    metaId: string;
    name: string;
    sbo: string;
    cvTerms: CVTerm[];
    history: History[];
    notes: string;
    xml: string;
    displaySId: string;
    sbaseType: string;
};

// doc
type SBMLDocument = {
    sbase: SBase;
    packages: {
        document: {
            level: number;
            version: number;
        };
        plugins: {
            prefix: string;
            version: number;
        }[];
    };
};

// model
type Model = {
    sbase: SBase;
    substanceUnits: string;
    timeUnits: string;
    volumeUnits: string;
    areaUnits: string;
    lengthUnits: string;
    extentUnits: string;
    conversionFactor: string;
};

// function definition
type FunctionDefinition = {
    sbase: SBase;
    math: mathDict;
};

// unit definition
type UnitDefinition = {
    sbase: SBase;
    listOfUnits: {
        nomTerms: {
            scale: number;
            multiplier: number;
            exponent: number;
            kind: {
                name: string;
            };
        }[];
        denomTerms: {
            scale: number;
            multiplier: number;
            exponent: number;
            kind: string;
        }[];
    }[];
};

type derivedUnits = {
    math: string;
    unitTerms: {
        scale: number;
        multiplier: number;
        exponent: number;
        kind: string;
    }[];
};

// compartment
type Compartment = {
    sbase: SBase;
    spatialDimensions: number;
    size: number;
    units: UnitDefinition; // add unit
    constant: boolean;
};

type Species = {
    sbase: SBase;
    compartment: Compartment;
    initialAmount: number;
    initialConcentration: number;
    substanceUnits: string;
    hasOnlySubstanceUnits: boolean;
    boundaryCondition: boolean;
    constant: boolean;
    conversionFactor: {
        sid: string;
        value: number;
        units: string;
    };
    fbc: {
        formula: string,
        charge: number;
    };
};

type Parameter = {
    sbase: SBase;
    value: number;
    units: derivedUnits;
    constant: boolean;
};

type InitialAssignment = {
    sbase: SBase;
    symbol: string;
    math: mathDict;
    units: derivedUnits;
};

type Rule = {
    sbase: SBase;
    variable: string;
    math: mathDict;
    units: derivedUnits;
};

type Constraint = {
    sbase: SBase;
    math: mathDict;
    message: string;
};

type Reaction = {
    sbase: SBase;
    reversible: boolean;
    compartment: Compartment;
    listOfReactants: {
        species: string;
        stoichiometry: number;
        constant: boolean;
    }[];
    listOfProducts: {
        species: string;
        stoichiometry: number;
        constant: boolean;
    }[];
    listOfModifiers: string[];
    fast: boolean;
    equation: string;
    kineticLaw: {
        math: mathDict;
        units: derivedUnits;
        listOfLocalParameters: {
            id: string;
            value: number;
            units: derivedUnits;
        }[];
    };
};

type Objective = {
    sbase: SBase;
    type: string;
    fluxObjectives: {
        sign: string;
        coefficient: number;
        reaction: Reaction;
    }[];
};

type Event = {
    sbase: SBase;
    useValuesFromTriggerTime: boolean;
    trigger: {
        math: mathDict;
        initialValue: number;
        persistent: boolean;
    };
    priority: mathDict;
    delay: mathDict;
    listOfEventAssignments: {
        variable: string;
        math: mathDict;
    }[];
};

type GeneProduct = {
    sbase: SBase;
    label: string;
    associatedSpecies: Species;
};

type sbaseRef = {
    sbase: SBase;
    portRef: string;
    idRef: string;
    unitRef: string;
    metaIdRef: string;
    referencedElement: {
        element: string;
        elementId: string;
    };
};

type SubModel = {
    sbase: SBase;
    modelRef: string;
    deletions: {
        type: string;
        value: string;
    }[];
    timeConversion: string;
    extentConversion: string;
};

type Port = {
    sbaseRef: sbaseRef;
};

type ModelInfo = {
    model: Model;
    submodels: SubModel[];
    ports: Port[];
    functionDefinitions: FunctionDefinition[];
    unitDefinitions: UnitDefinition[];
    compartments: Compartment[];
    species: Species[];
    parameters: Parameter[];
    initialAssignments: InitialAssignment[];
    rules: Rule[];
    constraints: Constraint[];
    reactions: Reaction[];
    objectives: Objective[];
    events: Event[];
    geneProducts: GeneProduct[];
};

type ModelDefinitions = Model[];

type Report = {
    doc: SBMLDocument;
    modelDefinitions: ModelDefinitions;
    debugInfo: {
        renderTime: string;
    };
};

export {
    SBase,
    SBMLDocument,
    Model,
    FunctionDefinition,
    UnitDefinition,
    Compartment,
    Species,
    Parameter,
    InitialAssignment,
    Rule,
    Constraint,
    Reaction,
    Objective,
    Event,
    GeneProduct,
    SubModel,
    Port,
    ModelInfo,
    ModelDefinitions,
    Report,
};
