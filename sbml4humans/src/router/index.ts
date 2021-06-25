import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import Home from "../views/Home.vue";
import UploadSBML from "../views/UploadSBML.vue";
import ExamplesList from "../views/ExamplesList.vue";
import Report from "../views/Report.vue";

const routes: Array<RouteRecordRaw> = [
    // landing page
    {
        path: "/",
        name: "Home",
        component: Home,
    },
    // page showing list of examples
    {
        path: "/examples",
        name: "ExamplesList",
        component: ExamplesList,
    },
    // page to upload SBML file
    {
        path: "/uploadSBML",
        name: "UploadSBML",
        component: UploadSBML,
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
