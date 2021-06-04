import { createStore } from "vuex";
import axios from "axios";
import router from "@/router";

import BASE_URLS from "@/data/urls";
import LIST_OF_EXAMPLES from "@/data/examples";

export default createStore({
    state: {
        // list of examples
        examples: LIST_OF_EXAMPLES.listOfExamples,

        // raw report
        rawReport: {},

        // final report
        jsonReport: {},

        // compartments
        compartments: [],

        // detail view info
        detailInfo: {},

        // describe if the model is still loading
        loading: false,
    },
    mutations: {
        SET_EXAMPLES(state, payload) {
            state.examples = payload;
        },
        SET_JSON_REPORT(state, payload) {
            state.jsonReport = payload;

            if (payload.report && payload.report.models) {
                const sbmlInfo = payload.report.models;
                const doc = payload.report.doc;

                state.detailInfo = doc;

                if (sbmlInfo.compartments) {
                    state.compartments = sbmlInfo.compartments;
                }
            }
        },
        SET_DETAIL_INFO(state, payload) {
            state.detailInfo = payload;
            console.log(state.detailInfo);
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
            console.log("INDEX 110");
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
