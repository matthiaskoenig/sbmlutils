import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import Home from "../views/Home.vue";
import UploadSBML from "../views/UploadSBML.vue";
import ExamplesList from "../views/ExamplesList.vue"

const routes: Array<RouteRecordRaw> = [
    {
        path: "/",
        name: "Home",
        component: Home,
    },
    {
        path: "/examples",
        name: "ExamplesList",
        component: ExamplesList,
    },
    {
        path: "/uploadSBML",
        name: "UploadSBML",
        component: UploadSBML,
    },
];

const router = createRouter({
    history: createWebHistory(process.env.BASE_URL),
    routes,
});

export default router;
