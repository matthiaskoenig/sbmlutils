const listOfSBMLTypes = [
    "SBMLDocument",
    "Submodel",
    "Port",
    "Model",
    "FunctionDefinition",
    "UnitDefinition",
    "Compartment",
    "Species",
    "Reaction",
    "Parameter",
    "InitialAssignment",
    "AssignmentRule",
    "RateRule", // not seen yet
    "Rule", // parent of Assignment Rule and Rate Rule
    "Objective",
    "Constraint",
    "Event",
    "GeneProduct",
];

export default {
    listOfSBMLTypes: listOfSBMLTypes,
};
