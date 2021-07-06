import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import Home from "../components/layout/Home.vue";
import Report from "../components/layout/Report.vue";

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
];

const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes,
});

export default router;
