import { createStore } from "vuex";
import axios from "axios";
import router from "@/router";

import BASE_URLS from "@/data/urls";
import TYPES from "@/data/sbmlComponents";
import MAPS from "@/data/allSBMLMap";

export default createStore({
    state: {
        // list of examples
        examples: [],

        // raw report (complete backend response)
        // contains both SBML report and Debug information
        rawData: TYPES.RawData,

        // final report
        jsonReport: TYPES.Report,

        // describe if the file report is still loading (REST endpoint)
        fileLoading: false,

        // describe if the example report is still loading (REST endpoint)
        exampleLoading: false,

        // message to show in loading container
        loadingMessage: "",

        /* For Search and Filter feature */
        visibility: {
            SBMLDocument: true,
            Submodel: true,
            Port: true,
            Model: true,
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

        counts: {
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
        },

        searchQuery: "",

        searchedSBasesPKs: new Set(),

        /* For Intercomponent Navigation */
        allObjectsMap: MAPS.objectsMap,

        componentPKsMap: MAPS.componentsMap,

        historyStack: [],

        stackPointer: 0,
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
        SET_LOADING_MESSAGE(state, payload) {
            state.loadingMessage = payload;
        },
        SET_STATIC(state, payload) {
            window.localStorage.setItem("static", payload);
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
        SET_SEARCHED_SBASES_PKS(state, payload) {
            state.searchedSBasesPKs = payload;
        },
        PUSH_TO_HISTORY_STACK(state, payload) {
            (state.historyStack as Array<string>).push(payload);
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
    },
    actions: {
        initializeReportView(context, payload) {
            // dump the raw data fetched from the backend
            context.commit("SET_RAW_DATA", payload.data);

            // update the SBML report to be rendered in the frontend
            context.commit("SET_JSON_REPORT", payload.data.report);

            // set the history stack to contain Doc pk by default
            this.dispatch("initializeHistoryStack", payload.data.report.doc.pk);

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
            context.commit("SET_LOADING_MESSAGE", "Loading Examples ...");

            // no queries to the API if static is ON
            if (window.localStorage.getItem("static") === "true") {
                alert(
                    "Cannot connect to API if Static is selected. Please switch off Static and refresh to fetch examples."
                );
                return;
            }

            context.commit("SET_EXAMPLE_LOADING", true);

            const url = BASE_URLS.API_BASE_URL + "/examples/";

            const res = await axios.get(url);

            context.commit("SET_EXAMPLE_LOADING", false);

            if (res.status === 200) {
                context.commit("SET_EXAMPLES", res.data.examples);
            } else {
                alert("Failed to fetch examples from API");
            }
        },
        // generate report for one particular example
        async fetchExampleReport(context, payload) {
            context.commit("SET_LOADING_MESSAGE", "Report is being generated ...");

            // no queries to the API if static is ON
            if (window.localStorage.getItem("static") === "true") {
                alert(
                    "Cannot connect to API if Static is selected. Please switch off Static and refresh to fetch report for this example."
                );
                return;
            }

            context.commit("SET_EXAMPLE_LOADING", true);

            const url = BASE_URLS.API_BASE_URL + "/examples/" + payload.exampleId;

            const res = await axios.get(url);

            context.commit("SET_EXAMPLE_LOADING", false);

            if (res.status === 200) {
                this.dispatch("initializeReportView", res);
            } else {
                alert("Failed to fetch example report from API");
            }
        },
        // generate report for uploaded SBML file
        async fetchReport(context, payload) {
            context.commit("SET_LOADING_MESSAGE", "Report is being generated ...");

            // no queries to the API if static is ON
            if (window.localStorage.getItem("static") === "true") {
                alert(
                    "Cannot connect to API if Static is selected. Please switch off Static and refresh to fetch report for this file."
                );
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
                this.dispatch("initializeReportView", res);
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
        updateSearchedSBasesPKs(context, payload) {
            context.commit("SET_SEARCHED_SBASES_PKS", payload);
        },
    },
    modules: {},
});
