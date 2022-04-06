import { createStore } from "vuex";
import axios from "axios";
import router from "@/router";

import INITIALIZATION_HELPERS from "@/helpers/reportInitialization";
import listOfSBMLTypes from "@/data/listOfSBMLTypes";
import { checkAPIResponse } from "@/helpers/additionalInfoUtils";
import sbmlComponents from "@/data/sbmlComponents";
import OMEX_HELPERS from "@/helpers/omexInitialization";

// read from .env.template file
export let VUE_APP_BASEURL = process.env.VUE_APP_BASEURL;
export let VUE_APP_APIURL = process.env.VUE_APP_APIURL;
export let VUE_APP_FRONTENDURL = process.env.VUE_APP_FRONTENDURL;

if (!VUE_APP_BASEURL) {
    // running in develop, no environment variable set
    VUE_APP_BASEURL = "http://0.0.0.0";
    VUE_APP_APIURL = "http://0.0.0.0:1444";
    VUE_APP_FRONTENDURL = "http://0.0.0.0:3456";
}

console.log("URL: " + VUE_APP_FRONTENDURL + " | " + VUE_APP_APIURL);

export default createStore({
    state: {
        // list of examples
        examples: [], // global

        // raw report (complete backend response)
        // contains both SBML report and Debug information
        rawData: {}, // report

        // final report
        currentReport: sbmlComponents.Report, // report

        // describe if the file report is still loading (REST endpoint)
        fileLoading: false, // report

        // describe if the example report is still loading (REST endpoint)
        exampleLoading: false, // report

        /* For core and comp functionality */
        currentModel: "", // report

        detailVisibility: false, // report

        /* For Search and Filter feature */
        visibility: {
            SBMLDocument: true,
            Submodel: true,
            Port: true,
            Model: true,
            ModelDefinition: true,
            ExternalModelDefinition: true,
            FunctionDefinition: true,
            UnitDefinition: true,
            Compartment: true,
            Species: true,
            Reaction: true,
            Parameter: true,
            InitialAssignment: true,
            AssignmentRule: true,
            RateRule: true,
            AlgebraicRule: true,
            Objective: true,
            Constraint: true,
            Event: true,
            GeneProduct: true,
        },

        searchQuery: "",

        searchedSBasesCounts: {
            SBMLDocument: 0,
            Submodel: 0,
            Port: 0,
            Model: 0,
            ModelDefinition: 0,
            ExternalModelDefinition: 0,
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
        },

        /* Report States */
        counts: {},
        allObjectsMap: {},
        componentPKsMap: {},
        componentWiseLists: {},

        historyStack: [],

        stackPointer: 0,

        currentFocussedTable: "",

        currentDocumentLocation: "",

        contexts: {},

        OMEXTree: {},
    },
    mutations: {
        SET_EXAMPLES(state, payload) {
            state.examples = payload;
        },
        SET_RAW_DATA(state, payload) {
            state.rawData = payload;
        },
        SET_CURRENT_REPORT(state, payload) {
            state.currentReport = payload;
        },
        SET_FILE_LOADING(state, payload) {
            state.fileLoading = payload;
        },
        SET_EXAMPLE_LOADING(state, payload) {
            state.exampleLoading = payload;
        },
        SET_DETAIL_VISIBILITY(state) {
            state.detailVisibility = !state.detailVisibility;
        },
        SET_STATIC(state, payload) {
            window.localStorage.setItem("static", payload);
        },
        SET_CURRENT_MODEL(state, payload) {
            state.currentModel = payload;
        },
        SET_VISIBILITY(state, payload) {
            state.visibility = payload;
        },
        SET_COUNTS(state, payload) {
            state.counts = payload;
        },
        SET_SEARCH_QUERY(state, payload) {
            state.searchQuery = payload;
        },
        SET_ALL_OBJECTS_MAP(state, payload) {
            state.allObjectsMap = payload;
        },
        SET_COMPONENT_PKS_MAP(state, payload) {
            state.componentPKsMap = payload;
        },
        SET_COMPONENT_WISE_LISTS(state, payload) {
            state.componentWiseLists = payload;
        },
        SET_SEARCHED_SBASES_COUNTS(state, payload) {
            state.searchedSBasesCounts = payload;
        },
        PUSH_TO_HISTORY_STACK(state, payload) {
            (state.historyStack as Array<string>).push(payload);
            state.detailVisibility = true;
        },
        MOVE_STACK_POINTER_BACK(state) {
            if (state.stackPointer > 0) {
                state.stackPointer--;
            }
        },
        MOVE_STACK_POINTER_FORWARD(state) {
            if (state.stackPointer < state.historyStack.length - 1) {
                state.stackPointer++;
            }
        },
        CLEAR_HISTORY_STACK(state) {
            state.historyStack = [];
            state.stackPointer = 0;
        },
        SET_CURRENT_FOCUSSED_TABLE(state, payload) {
            state.currentFocussedTable = payload;
        },
        SET_CONTEXTS(state, payload) {
            state.contexts = payload;
        },
        SET_OMEX_TREE(state, payload) {
            state.OMEXTree = payload;
        },
        SET_CURRENT_DOCUMENT_LOCATION(state, payload) {
            state.currentDocumentLocation = payload;
        },
    },
    actions: {
        updateCurrentModel(context, payload) {
            context.commit("SET_CURRENT_MODEL", payload);
        },
        initializeReport(context, payload) {
            // dump the raw data fetched from the backend
            const OMEXRes = payload.data;
            context.commit("SET_RAW_DATA", OMEXRes);

            const OMEXTree = OMEX_HELPERS.generateOMEXTree(OMEXRes);
            context.commit("SET_OMEX_TREE", OMEXTree);

            const initializationData =
                INITIALIZATION_HELPERS.organizeLocationwiseContexts(OMEXRes) as Record<
                    string,
                    unknown
                >;

            const contexts = initializationData["contexts"] as Record<string, unknown>;
            context.commit("SET_CONTEXTS", contexts);

            // update the SBML report and other states to be rendered in the frontend
            this.dispatch(
                "updateReportStatesAndFollowUp",
                contexts[initializationData["initialReportLocation"] as string]
            );

            this.dispatch(
                "updateCurrentDocumentLocation",
                initializationData["initialReportLocation"] as string
            );

            // redirect to report view
            router.push("/report");
        },
        updateReportStatesAndFollowUp(context, payload) {
            context.commit("SET_CURRENT_REPORT", payload["report"]);
            this.dispatch("updateCounts", payload["counts"]);
            this.dispatch("updateAllObjectsMap", payload["allObjectsMap"]);
            this.dispatch("updateComponentPKsMap", payload["componentPKsMap"]);
            this.dispatch("updateComponentWiseLists", payload["componentWiseLists"]);

            // set the current model to main model in the report by default
            const currentReport = context.state.currentReport;
            if (!currentReport.model) {
                alert("No model in file ! Check if file is a valid SBML file.");
            }

            this.dispatch("updateCurrentModel", currentReport.model.pk);
            this.dispatch("updateCurrentFocussedTable", "");
            this.dispatch("updateSearchQuery", "");

            // set the history stack to contain Doc pk by default
            this.dispatch("initializeHistoryStack", currentReport.doc.pk);
            this.dispatch("toggleDetailVisibility");
        },
        updateCurrentDocumentLocation(context, payload) {
            context.commit("SET_CURRENT_DOCUMENT_LOCATION", payload);
        },
        pushToHistoryStack(context, payload) {
            context.commit("PUSH_TO_HISTORY_STACK", payload);
            context.commit("MOVE_STACK_POINTER_FORWARD");
        },
        initializeHistoryStack(context, payload) {
            context.commit("CLEAR_HISTORY_STACK");
            this.dispatch("pushToHistoryStack", payload);
        },
        moveStackPointerBack(context) {
            context.commit("MOVE_STACK_POINTER_BACK");
        },
        moveStackPointerForward(context) {
            context.commit("MOVE_STACK_POINTER_FORWARD");
        },
        // get list of all available examples from backend API
        async fetchExamples(context) {
            const url = VUE_APP_APIURL + "/examples";
            const res = await axios.get(url);
            if (res.status === 200) {
                checkAPIResponse(res);
                res.data.examples.forEach((example) => {
                    example["searchUtilField"] =
                        example.id +
                        example.name +
                        example.description +
                        example.packages.join(",");
                });
                context.commit("SET_EXAMPLES", res.data.examples);
            } else {
                console.log("Failed to fetch examples from API");
            }
        },
        // generate report for one particular example
        async fetchExampleReport(context, payload) {
            context.commit("SET_EXAMPLE_LOADING", true);
            const url = VUE_APP_APIURL + "/examples/" + payload.exampleId;
            const res = await axios.get(url);

            context.commit("SET_EXAMPLE_LOADING", false);

            if (res.status === 200) {
                // console.log(res);
                checkAPIResponse(res);
                this.dispatch("initializeReport", res);
            } else {
                console.log("Failed to fetch example report from API");
            }
        },
        // generate report for uploaded SBML file
        async fetchReport(context, payload) {
            context.commit("SET_FILE_LOADING", true);

            // assembling the request parameters
            const url = VUE_APP_APIURL + "/file";
            const formData = payload.formData;
            const headers = payload.headers;

            const res = await axios.post(url, formData, headers);

            context.commit("SET_FILE_LOADING", false);

            if (res.status === 200) {
                checkAPIResponse(res);
                this.dispatch("initializeReport", res);
            } else {
                console.log("Failed to fetch report from API.");
            }
        },
        // generate report for uploaded SBML file using model URL
        async fetchReportUsingURL(context, payload) {
            context.commit("SET_FILE_LOADING", true);

            // assembling the request parameters
            const url = VUE_APP_APIURL + "/url?url=" + payload;
            console.log("Create report for url: " + url);
            const res = await axios.get(url);

            context.commit("SET_FILE_LOADING", false);

            if (res.status === 200) {
                checkAPIResponse(res);
                this.dispatch("initializeReport", res);
            } else {
                console.log("Failed to fetch report from API.");
            }
        },
        // generate report for pasted SBML content
        async fetchReportUsingSBMLContent(context, payload) {
            context.commit("SET_FILE_LOADING", true);

            // assembling the request parameters
            const url = VUE_APP_APIURL + "/content";
            const res = await axios.post(url, payload);

            context.commit("SET_FILE_LOADING", false);

            if (res.status === 200) {
                checkAPIResponse(res);
                this.dispatch("initializeReport", res);
            } else {
                console.log("Failed to fetch report from API.");
            }
        },
        // update the detailInfo to show new data in the detail view box
        updateDetailInfo(context, payload) {
            context.commit("SET_DETAIL_INFO", payload);
        },
        // update the static flag according to the state of the switch on the navbar
        updateStatic(context, payload) {
            context.commit("SET_STATIC", payload);
        },
        toggleDetailVisibility(context) {
            context.commit("SET_DETAIL_VISIBILITY");
        },
        updateVisibility(context, payload) {
            context.commit("SET_VISIBILITY", payload);
        },
        // update counts of SBML components as calculated in ListOfSBases
        updateCounts(context, payload) {
            context.commit("SET_COUNTS", payload);
        },
        updateSearchQuery(context, payload) {
            context.commit("SET_SEARCH_QUERY", payload);
        },
        updateAllObjectsMap(context, payload) {
            context.commit("SET_ALL_OBJECTS_MAP", payload);
        },
        updateComponentPKsMap(context, payload) {
            context.commit("SET_COMPONENT_PKS_MAP", payload);
        },
        updateComponentWiseLists(context, payload) {
            context.commit("SET_COMPONENT_WISE_LISTS", payload);
        },
        updateSearchedSBasesCounts(context, payload) {
            context.commit("SET_SEARCHED_SBASES_COUNTS", payload);
        },
        updateCurrentFocussedTable(context, payload) {
            context.commit("SET_CURRENT_FOCUSSED_TABLE", payload);
        },
    },

    getters: {
        componentPKsMap(state) {
            return state.componentPKsMap[state.currentModel];
        },
        counts(state) {
            return state.counts[state.currentModel];
        },
        reportBasics(state) {
            const basicComponents: Array<Record<string, unknown>> = [];
            basicComponents.push(
                state.allObjectsMap[state.componentWiseLists["SBMLDocument"][0]]
            );

            const componentPKsMap = state.componentPKsMap;
            for (const modelPK in componentPKsMap) {
                basicComponents.push(state.allObjectsMap[modelPK]);
            }

            return basicComponents;
        },
        sbases(state, getters) {
            const modelComponentsMap = getters.componentPKsMap as Record<
                string,
                Array<string>
            >;

            const sbases: Array<Record<string, unknown>> = [];
            listOfSBMLTypes.listOfSBMLTypes.forEach((key) => {
                const componentPKs = modelComponentsMap[key];
                if (componentPKs) {
                    componentPKs.forEach((pk) => {
                        sbases.push(state.allObjectsMap[pk]);
                    });
                }
            });
            return sbases;
        },
        tables(state) {
            const componentPKsList = {} as Record<string, Array<string>>;
            listOfSBMLTypes.listOfSBMLTypes.forEach((sbmlType) => {
                componentPKsList[sbmlType] = [];
                for (const modelPK in state.componentPKsMap) {
                    if (state.componentPKsMap[modelPK][sbmlType]) {
                        componentPKsList[sbmlType].push(
                            ...state.componentPKsMap[modelPK][sbmlType]
                        );
                    }
                }
            });
            return componentPKsList;
        },
        OMEXTree(state) {
            return state.OMEXTree;
        },
    },
});
