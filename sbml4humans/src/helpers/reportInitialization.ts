import store from "@/store/index";
import allSBML from "@/data/allSBMLMap";
import listOfSBMLTypes from "@/data/listOfSBMLTypes";

function addSearchUtilityField(sbase: Record<string, unknown>): void {
    let searchUtilField = "";
    for (const key in sbase) {
        if (key === "xml") {
            continue;
        }
        searchUtilField += sbase[key] + " ";
    }
    sbase["searchUtilField"] = searchUtilField;
}

function initializeComponentWiseLists(): Record<string, Array<string>> {
    const map = {};
    listOfSBMLTypes.listOfSBMLTypes.forEach((sbmlType) => {
        map[sbmlType] = [];
    });
    return map;
}

function organizeLocationwiseContexts(
    OMEXRes: Record<string, unknown>
): Record<string, unknown> {
    const contexts = {};
    let initialReportLocation = "";

    const reports = OMEXRes["reports"] as Record<string, unknown>;
    let i = 0;
    for (const location in reports) {
        if (i++ == 0) {
            initialReportLocation = location;
        }
        contexts[location] = assembleSBasesInReport(
            (reports[location] as Record<string, unknown>)["report"] as Record<
                string,
                unknown
            >
        );
        contexts[location]["report"] = (reports[location] as Record<string, unknown>)[
            "report"
        ];
    }

    return {
        contexts: contexts,
        initialReportLocation: initialReportLocation,
    };
}

/**
 * Collects the SBML Document and all model definitions from the backend API
 * response. It then collects other SBML objects in these definitions. Also
 * updates the count of SBML components and initializes global component maps.
 * @param report The generated SBML report sent in the API response.
 */
function assembleSBasesInReport(
    report: Record<string, unknown>
): Record<string, unknown> {
    if (report === null) {
        return {};
    }

    const sbases: Array<Record<string, unknown>> = [];
    const counts: Record<string, Record<string, number>> = {};
    const allObjectsMap: Record<string, unknown> = {}; // object lookup map
    const componentPKsMap: Record<string, Record<string, Array<string>>> = {};
    const componentWiseLists: Record<
        string,
        Array<string>
    > = initializeComponentWiseLists();

    // collecting doc
    if (report.doc) {
        addSearchUtilityField(report.doc as Record<string, unknown>);
        sbases.push(report.doc as Record<string, unknown>);
        allObjectsMap[(report.doc as Record<string, unknown>).pk as string] =
            report.doc;
        componentWiseLists["SBMLDocument"] = [
            (report.doc as Record<string, unknown>).pk as string,
        ];
    }

    const model: Record<string, unknown> = report.model as Record<string, unknown>;
    const modelPK = model.pk as string;

    if (model) {
        addSearchUtilityField(model);
        componentWiseLists["Model"].push(modelPK);

        counts[modelPK] = allSBML.counts;

        counts[modelPK]["Model"] = 1;

        sbases.push(model);

        allObjectsMap[modelPK] = model;
        componentPKsMap[modelPK] = {};

        componentPKsMap[modelPK]["Model"] = [modelPK];

        // collecting all other components
        sbases.push(
            ...collectSBasesInModel(
                model,
                counts,
                allObjectsMap,
                componentPKsMap,
                componentWiseLists
            )
        );
    }

    const modelTypes = ["modelDefinitions", "externalModelDefinitions"];
    componentPKsMap[modelPK]["ExternalModelDefinition"] = [];
    componentPKsMap[modelPK]["ModelDefinition"] = [];

    modelTypes.forEach((modelType) => {
        if (report[modelType]) {
            const modelDefinitions = report[modelType] as Array<
                Record<string, unknown>
            >;
            for (let i = 0; i < modelDefinitions.length; i++) {
                const md = modelDefinitions[i];
                addSearchUtilityField(md);
                const pk = md.pk as string;

                const sbmlType =
                    modelType.charAt(0).toUpperCase() +
                    modelType.slice(1, modelType.length - 1);
                componentPKsMap[modelPK][sbmlType].push(pk);
                counts[modelPK][sbmlType]++;

                counts[pk] = {};
                componentPKsMap[pk] = {};

                counts[pk]["Model"] = 1;

                allObjectsMap[pk] = md;
                componentPKsMap[pk]["Model"] = [pk];
                componentWiseLists[sbmlType].push(pk); // look here next time to add modeldefs to models table

                // collecting all other components
                sbases.push(
                    ...collectSBasesInModel(
                        md,
                        counts,
                        allObjectsMap,
                        componentPKsMap,
                        componentWiseLists
                    )
                );
            }
        }
    });

    store.dispatch("updateCounts", counts);
    store.dispatch("updateAllObjectsMap", allObjectsMap);
    store.dispatch("updateComponentPKsMap", componentPKsMap);
    store.dispatch("updateComponentWiseLists", componentWiseLists);

    const contextForReport = {
        counts: counts,
        allObjectsMap: allObjectsMap,
        componentPKsMap: componentPKsMap,
        componentWiseLists: componentWiseLists,
    };

    return contextForReport;
}

/**
 * Collects SBML objects inside a particular model definition.
 *
 * @param model The SBML model
 * @param counts Global counts map
 * @param allObjectsMap Global map for all SBML objects
 * @param componentPKsMap Global map for component-wise SBML objects
 */
function collectSBasesInModel(
    model: Record<string, unknown>,
    counts: Record<string, Record<string, number>>,
    allObjectsMap: Record<string, unknown>,
    componentPKsMap: Record<string, Record<string, Array<unknown>>>,
    componentWiseLists: Record<string, Array<string>>
): Array<Record<string, unknown>> {
    const sbasesInModel: Array<Record<string, unknown>> = [];

    for (let i = 0; i < listOfSBMLTypes.listOfSBMLTypes.length; i++) {
        const sbmlType = listOfSBMLTypes.listOfSBMLTypes[i];

        // camel case keys, present in the API response E.g. unitDefinitions, compartments
        let key: string = sbmlType.charAt(0).toLowerCase() + sbmlType.slice(1);
        if (sbmlType != "Species") {
            key = key + "s";
        }

        if (model[key]) {
            const component: Array<Record<string, unknown>> = model[key] as Array<
                Record<string, unknown>
            >;

            componentPKsMap[model.pk as string][sbmlType] = [];

            counts[model.pk as string][sbmlType] = component.length as number;
            component.forEach((sbase) => {
                addSearchUtilityField(sbase);
                sbasesInModel.push(sbase);

                const pk = sbase.pk as string;
                allObjectsMap[pk] = sbase;
                componentPKsMap[model.pk as string][sbmlType].push(pk);
                componentWiseLists[sbmlType].push(pk);
            });
        }
    }

    return sbasesInModel;
}

export default {
    organizeLocationwiseContexts: organizeLocationwiseContexts,
    assembleSBasesInReport: assembleSBasesInReport,
};
