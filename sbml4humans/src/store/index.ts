import { createStore } from "vuex";
import axios from "axios";
import router from "@/router";

import BASE_URLS from "@/data/urls";
import LIST_OF_EXAMPLES from "@/data/examples";

export default createStore({

    // FIXME: use the identical variable names between JSON & state/internals

    state: {
        // list of examples
        // FIXME: query examples from python backend
        examples: LIST_OF_EXAMPLES.listOfExamples,

        // FIXME: add a static flag/switch
        //e.g. do not show/query examples & upload SBML in static mode
        // if static is activated: => no queries to the endpoint;
        // no debug information in static;

        // raw report (complete backend response)
        // FIXME: split in "debug"
        rawReport: {},

        // final report
        // FIXME: call in "report"
        jsonReport: {},

        // compartments (helper state variable)
        compartments: [],

        // detail view info (for access from every where)
        detailInfo: {},

        // describe if the model is still loading (REST endpoint)
        loading: false,
    },
    mutations: {
        SET_EXAMPLES(state, payload) {
            state.examples = payload;
        },
        SET_JSON_REPORT(state, payload) {
            state.jsonReport = payload;

            if (payload.report && payload.report.models) {
                const doc = payload.report.doc;
                const models = payload.report.models;

                state.detailInfo = doc;

                if (models.compartments) {
                    state.compartments = models.compartments;
                }
            }
        },
        SET_DETAIL_INFO(state, payload) {
            state.detailInfo = payload;
        },
        SET_LOADING_STATUS(state, payload) {
            state.loading = payload;
        },
    },
    actions: {
        // get list of all examples available
        async fetchExamples(context) {
            context.commit("SET_LOADING_STATUS", true);

            const url = BASE_URLS.API_BASE_URL + "/examples/list";

            const res = await axios.get(url);

            context.commit("SET_LOADING_STATUS", false);
            if (res.status === 200) {
                context.commit("SET_EXAMPLES", res.data.examples);
            } else {
                alert("Failed to fetch examples from API");
            }
        },
        // generate report for one particular example
        async fetchExampleReport(context, payload) {
            context.commit("SET_LOADING_STATUS", true);

            const url = BASE_URLS.API_BASE_URL + "/examples/" + payload.exampleId;

            const res = await axios.get(url);

            context.commit("SET_LOADING_STATUS", false);

            if (res.status === 200) {
                context.commit("SET_JSON_REPORT", res.data);
                context.commit("SET_DETAIL_INFO", res.data.report.doc);
                router.replace("report");
            } else {
                alert("Failed to fetch example report from API");
            }
        },
        // generate report for uploaded SBML file
        async fetchReport(context, payload) {
            context.commit("SET_LOADING_STATUS", true);

            const url = BASE_URLS.API_BASE_URL + "/sbml";

            const formData = payload.formData;
            const headers = payload.headers;

            const res = await axios.post(url, formData, headers);

            context.commit("SET_LOADING_STATUS", false);

            if (res.status === 200) {
                context.commit("SET_JSON_REPORT", res.data);
                context.commit("SET_DETAIL_INFO", res.data.report.doc);
                router.replace("report");
            } else {
                alert("Failed to fetch report from API.");
            }
        },
        updateDetailInfo(context, payload) {
            context.commit("SET_DETAIL_INFO", payload);
        },
    },
    getters: {
        getJSONReport(state) {
            return state.jsonReport;
        },
    },
    modules: {},
});
