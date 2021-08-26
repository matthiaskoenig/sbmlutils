import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import Home from "../components/layout/Home.vue";
import Report from "../components/layout/Report.vue";
import store from "@/store/index";

const routes: Array<RouteRecordRaw> = [
    // landing page
    {
        path: "/",
        name: "Home",
        component: Home,
    },
    // page showing the rendered report
    {
        path: "/report",
        name: "Report",
        component: Report,
    },
    // getting report using model URL
    {
        path: "/model_url",
        name: "ModelPath",
        component: Home,
        beforeEnter(to) {
            store.dispatch("fetchReportUsingURL", to.query.url);
        },
    },
];

const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes,
});

export default router;
