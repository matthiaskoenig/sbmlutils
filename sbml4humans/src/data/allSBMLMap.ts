const counts = {
    SBMLDocument: 0,
    Submodel: 0,
    Port: 0,
    Model: 0,
    FunctionDefinition: 0,
    UnitDefinition: 0,
    Compartment: 0,
    Species: 0,
    Reaction: 0,
    Parameter: 0,
    InitialAssignment: 0,
    AssignmentRule: 0,
    RateRule: 0,
    AlgebraicRule: 0,
    Objective: 0,
    Constraint: 0,
    Event: 0,
    GeneProduct: 0,
};

const objectsMap = {
    SBMLDocument: {},
    Submodel: {},
    Port: {},
    Model: {},
    FunctionDefinition: {},
    UnitDefinition: {},
    Compartment: {},
    Species: {},
    Reaction: {},
    Parameter: {},
    InitialAssignment: {},
    AssignmentRule: {},
    RateRule: {},
    AlgebraicRule: {},
    Objective: {},
    Constraint: {},
    Event: {},
    GeneProduct: {},
};

const listOfComponentsByModel = {
    SBMLDocument: [],
    Submodel: [],
    Port: [],
    Model: [],
    FunctionDefinition: [],
    UnitDefinition: [],
    Compartment: [],
    Species: [],
    Reaction: [],
    Parameter: [],
    InitialAssignment: [],
    AssignmentRule: [],
    RateRule: [],
    AlgebraicRule: [],
    Objective: [],
    Constraint: [],
    Event: [],
    GeneProduct: [],
};

const componentsMap = {
    model: listOfComponentsByModel,
};

export default {
    counts: counts,
    objectsMap: objectsMap,
    listOfComponentsByModel: listOfComponentsByModel,
    componentsMap: componentsMap,
};
