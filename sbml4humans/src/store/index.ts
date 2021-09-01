import { createStore } from "vuex";
import axios from "axios";
import router from "@/router";

import BASE_URLS from "@/data/urls";
import INITIALIZATION_HELPERS from "@/helpers/reportInitialization";
import listOfSBMLTypes from "@/data/listOfSBMLTypes";

const static_alert =
    "Cannot connect to API in 'static' mode. Switch off 'static' and refresh.";

export default createStore({
    state: {
        // list of examples
        examples: [], // global

        // raw report (complete backend response)
        // contains both SBML report and Debug information
        rawData: {}, // report

        // final report
        jsonReport: {}, // report

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

        counts: {},

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

        /* For Intercomponent Navigation */
        allObjectsMap: {},

        componentPKsMap: {},

        componentWiseLists: {},

        historyStack: [],

        stackPointer: 0,

        currentFocussedTable: "",
    },
    mutations: {
        SET_EXAMPLES(state, payload) {
            state.examples = payload;
        },
        SET_RAW_DATA(state, payload) {
            state.rawData = payload;
        },
        SET_JSON_REPORT(state, payload) {
            state.jsonReport = payload;
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
    },
    actions: {
        updateCurrentModel(context, payload) {
            context.commit("SET_CURRENT_MODEL", payload);
        },
        initializeReport(context, payload) {
            // dump the raw data fetched from the backend
            context.commit("SET_RAW_DATA", payload.data);

            // update the SBML report to be rendered in the frontend
            context.commit("SET_JSON_REPORT", payload.data.report);

            // set the current model to main model in the report by default
            this.dispatch("updateCurrentModel", payload.data.report.model.pk);
            this.dispatch("updateCurrentFocussedTable", "");

            INITIALIZATION_HELPERS.assembleSBasesInReport(payload.data.report);

            // set the history stack to contain Doc pk by default
            this.dispatch("initializeHistoryStack", payload.data.report.doc.pk);
            this.dispatch("toggleDetailVisibility");

            // redirect to report view
            router.push("/report");
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
            // no queries to the API if static is ON
            if (window.localStorage.getItem("static") === "true") {
                alert(static_alert);
                return;
            }

            const url = BASE_URLS.API_BASE_URL + "/examples/";

            const res = await axios.get(url);

            if (res.status === 200) {
                res.data.examples.forEach((example) => {
                    example["searchUtilField"] =
                        example.id +
                        example.description +
                        example.keywords.join(",") +
                        example.packages.join(",");
                });
                context.commit("SET_EXAMPLES", res.data.examples);
            } else {
                alert("Failed to fetch examples from API");
            }
        },
        // generate report for one particular example
        async fetchExampleReport(context, payload) {
            // no queries to the API if static is ON
            if (window.localStorage.getItem("static") === "true") {
                alert(static_alert);
                return;
            }

            context.commit("SET_EXAMPLE_LOADING", true);

            const url = BASE_URLS.API_BASE_URL + "/examples/" + payload.exampleId;

            const res = await axios.get(url);

            context.commit("SET_EXAMPLE_LOADING", false);

            if (res.status === 200) {
                this.dispatch("initializeReport", res);
            } else {
                alert("Failed to fetch example report from API");
            }
        },
        // generate report for uploaded SBML file
        async fetchReport(context, payload) {
            // no queries to the API if static is ON
            if (window.localStorage.getItem("static") === "true") {
                alert(static_alert);
                return;
            }

            context.commit("SET_FILE_LOADING", true);

            // assembling the request parameters
            const url = BASE_URLS.API_BASE_URL + "/sbml";
            const formData = payload.formData;
            const headers = payload.headers;

            const res = await axios.post(url, formData, headers);

            context.commit("SET_FILE_LOADING", false);

            if (res.status === 200) {
                this.dispatch("initializeReport", res);
            } else {
                alert("Failed to fetch report from API.");
            }
        },
        // generate report for uploaded SBML file using model URL
        async fetchReportUsingURL(context, payload) {
            // no queries to the API if static is ON
            if (window.localStorage.getItem("static") === "true") {
                alert(static_alert);
                return;
            }

            context.commit("SET_FILE_LOADING", true);

            // assembling the request parameters
            const url = BASE_URLS.API_BASE_URL + "/model_urls?url=" + payload;

            const res = await axios.get(url);

            context.commit("SET_FILE_LOADING", false);

            if (res.status === 200) {
                this.dispatch("initializeReport", res);
            } else {
                alert("Failed to fetch report from API.");
            }
        },
        // generate report for pasted SBML content
        async fetchReportUsingSBMLContent(context, payload) {
            // no queries to the API if static is ON
            if (window.localStorage.getItem("static") === "true") {
                alert(static_alert);
                return;
            }

            context.commit("SET_FILE_LOADING", true);

            // assembling the request parameters
            const url = BASE_URLS.API_BASE_URL + "/sbml_content";

            const res = await axios.post(url, payload);

            context.commit("SET_FILE_LOADING", false);

            if (res.status === 200) {
                this.dispatch("initializeReport", res);
            } else {
                alert("Failed to fetch report from API.");
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
    modules: {},
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
    },
});
