import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import Home from "../components/layout/Home.vue";
import Report from "../components/layout/Report.vue";
import About from "../components/layout/About.vue";
import Examples from "../components/layout/Examples.vue";
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
    {
        path: "/about",
        name: "About",
        component: About,
    },
    {
        path: "/examples",
        name: "Examples",
        component: Examples,
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
