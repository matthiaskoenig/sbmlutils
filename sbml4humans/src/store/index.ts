import { createStore } from "vuex";
import axios from "axios";
import router from "@/router";

import BASE_URLS from "@/data/urls";
import TYPES from "@/sbmlComponents";
import colorScheme from "@/data/colorScheme";

export default createStore({
    state: {
        // list of examples
        examples: [],

        // raw report (complete backend response)
        // contains both SBML report and Debug information
        rawData: TYPES.RawData,

        // final report
        // FIXME: call in "report"
        jsonReport: TYPES.Report,

        // detail view info (for access from every where)
        detailInfo: {},

        // describe if the file report is still loading (REST endpoint)
        fileLoading: false,

        // describe if the file report is still loading (REST endpoint)
        exampleLoading: false,

        // FIXME: add a static flag/switch
        //e.g. do not show/query examples & upload SBML in static mode
        // if static is activated: => no queries to the endpoint;
        // no debug information in static;
        // UPDATE: static has been migrated to localStorage

        /* For Search and Filter feature */

        visibility: {
            SBMLDocument: true,
            SubModel: true,
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
            Rule: true,
            Objective: true,
            Constraint: true,
            Event: true,
            GeneProduct: true,
        },

        counts: {
            SBMLDocument: 0,
            SubModel: 0,
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
            Rule: 0,
            Objective: 0,
            Constraint: 0,
            Event: 0,
            GeneProduct: 0,
        },

        searchQuery: null,
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
        SET_DETAIL_INFO(state, payload) {
            state.detailInfo = payload;
        },
        SET_FILE_LOADING(state, payload) {
            state.fileLoading = payload;
        },
        SET_EXAMPLE_LOADING(state, payload) {
            state.exampleLoading = payload;
        },
        SET_STATIC(state, payload) {
            /* the localStorage stores selected static state to maintain it accross
               page refreshes. We can plan on extending this feature to jsonReport and detailInfo too perhaps. */
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
    },
    actions: {
        // get list of all available examples from backend API
        async fetchExamples(context) {
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
                // DEBUGGING ATTEMPTS FOR ICG_BODY AND ICG_BODY_FLAT
                //console.log(res.data);
                // let strRes = JSON.stringify(res.data);
                // strRes = strRes.replace(/\\n/g, "\n").replace(/\\/g, "");

                // strRes = String(strRes);
                // console.log(strRes);

                // const stRes = JSON.parse(strRes);
                // console.log(stRes);
                // // console.log(Object.keys(stRes));

                // dump the raw data fetched from the backend
                context.commit("SET_RAW_DATA", res.data);

                // update the SBML report to be rendered in the frontend
                context.commit("SET_JSON_REPORT", res.data.report);

                // set the detail view to show Doc information by default
                context.commit("SET_DETAIL_INFO", res.data.report.doc);

                // redirect to report view
                router.push("/report");
            } else {
                alert("Failed to fetch example report from API");
            }
        },
        // generate report for uploaded SBML file
        async fetchReport(context, payload) {
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
                // dump the raw data fetched from the backend
                context.commit("SET_RAW_DATA", res.data);

                // update the SBML report to be rendered in the frontend
                context.commit("SET_JSON_REPORT", res.data.report);

                // set the detail view to show Doc information by default
                context.commit("SET_DETAIL_INFO", res.data.report.doc);

                // redirect to report view
                router.push("/report");
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
    },
    modules: {},
});
