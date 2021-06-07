import { createStore } from "vuex";
import axios from "axios";
import router from "@/router";

import BASE_URLS from "@/data/urls";
import TYPES from "@/sbmlComponents";

export default createStore({
    // FIXME: use the identical variable names between JSON & state/internals

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

        // describe if the model is still loading (REST endpoint)
        loading: false,

        // FIXME: add a static flag/switch
        //e.g. do not show/query examples & upload SBML in static mode
        // if static is activated: => no queries to the endpoint;
        // no debug information in static;
        static: localStorage.static,
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
        SET_LOADING(state, payload) {
            state.loading = payload;
        },
        SET_STATIC(state, payload) {
            state.static = payload;

            /* the localStorage stores previously selected Static state to maintain it accross
               page refreshes. We can plan on extending this feature to jsonReport and detailInfo too perhaps. */
            localStorage.static = state.static;
        },
    },
    actions: {
        // get list of all available examples from backend API
        async fetchExamples(context) {
            // no queries to the API if static is ON
            if (this.state.static === true) {
                alert(
                    "Cannot connect to API if Static is selected. Please switch off Static and refresh to fetch examples."
                );
                return;
            }

            context.commit("SET_LOADING", true);

            const url = BASE_URLS.API_BASE_URL + "/examples/list";

            const res = await axios.get(url);

            context.commit("SET_LOADING", false);

            if (res.status === 200) {
                context.commit("SET_EXAMPLES", res.data.examples);
            } else {
                alert("Failed to fetch examples from API");
            }
        },
        // generate report for one particular example
        async fetchExampleReport(context, payload) {
            // no queries to the API if static is ON
            if (this.state.static === true) {
                alert(
                    "Cannot connect to API if Static is selected. Please switch off Static and refresh to fetch report for this example."
                );
                return;
            }

            context.commit("SET_LOADING", true);

            const url = BASE_URLS.API_BASE_URL + "/examples/" + payload.exampleId;

            const res = await axios.get(url);

            context.commit("SET_LOADING", false);

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
                alert("Failed to fetch example report from API");
            }
        },
        // generate report for uploaded SBML file
        async fetchReport(context, payload) {
            // no queries to the API if static is ON
            if (this.state.static === true) {
                alert(
                    "Cannot connect to API if Static is selected. Please switch off Static and refresh to fetch report for this file."
                );
                return;
            }

            context.commit("SET_LOADING", true);

            // assembling the request parameters
            const url = BASE_URLS.API_BASE_URL + "/sbml";
            const formData = payload.formData;
            const headers = payload.headers;

            const res = await axios.post(url, formData, headers);

            context.commit("SET_LOADING", false);

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
    },
    getters: {
        getExamples(state) {
            return state.examples;
        },
        getRawData(state) {
            return state.rawData;
        },
        getJSONReport(state) {
            return state.jsonReport;
        },
        getDetailInfo(state) {
            return state.detailInfo;
        },
        getLoadingStatus(state) {
            return state.loading;
        },
        getStaticFlag(state) {
            return state.static;
        },
    },
    modules: {},
});
