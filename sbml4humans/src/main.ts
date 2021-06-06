import { createApp } from "vue";
import App from "./App.vue";
import "./registerServiceWorker";
import router from "./router";
import store from "./store";

// bootstrap
import Antd from "ant-design-vue";
import 'ant-design-vue/dist/antd.css';
import "../node_modules/bootstrap/dist/css/bootstrap.css";
import "../node_modules/bootstrap/dist/js/bootstrap.bundle.js";
import "../node_modules/jquery/src/jquery.js";
//import { Vue } from "vue";

//import Compartment from "@/components/sbml/Compartment.vue";

//App.component("Compartment", Compartment);

createApp(App).use(store).use(router).use(Antd).mount("#app");
