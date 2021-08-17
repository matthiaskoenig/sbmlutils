/* Color Scheme of the different components in the SBML Suite */

const componentColor = {
    SBMLDocument: "#fee090",
    Submodel: "#00ccff",
    Port: "#fed9a6",
    Model: "#66c2a5",
    ModelDefinition: "#66c2a5",
    ExternalModelDefinition: "#66c2a5",
    FunctionDefinition: "#e6f598",
    UnitDefinition: "#f1b6da",
    Compartment: "#92c5de",
    Species: "#abdda4",
    Reaction: "#a6cee3",
    Parameter: "#fdae61",
    InitialAssignment: "#fee08b",
    AssignmentRule: "#fb9a99",
    RateRule: "#fb9a99",
    AlgebraicRule: "#fb9a99",
    Objective: "#f46d43",
    Constraint: "#fdae61",
    Event: "#fee08b",
    GeneProduct: "#d53e4f",
} as { [key: string]: string };

// const componentColor = {
//     SBMLDocument: "#ffffff",
//     Submodel: "#ffffff",
//     Port: "#ffffff",
//     Model: "#ffffff",
//     ModelDefinition: "#ffffff",
//     ExternalModelDefinition: "#ffffff",
//     FunctionDefinition: "#ffffff",
//     UnitDefinition: "#ffffff",
//     Compartment: "#ffffff",
//     Species: "#ffffff",
//     Reaction: "#ffffff",
//     Parameter: "#ffffff",
//     InitialAssignment: "#ffffff",
//     AssignmentRule: "#ffffff",
//     RateRule: "#ffffff",
//     AlgebraicRule: "#ffffff",
//     Objective: "#ffffff",
//     Constraint: "#ffffff",
//     Event: "#ffffff",
//     GeneProduct: "#ffffff",
// } as { [key: string]: string };

export default {
    componentColor: componentColor,
};
