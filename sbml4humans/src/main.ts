import { createApp } from "vue";
import App from "./App.vue";
import "./registerServiceWorker";
import router from "./router";
import store from "./store";

// bootstrap
import { List } from "ant-design-vue";
import "ant-design-vue/dist/antd.css";
import "../node_modules/bootstrap/dist/css/bootstrap.css";
import "../node_modules/bootstrap/dist/js/bootstrap.bundle.js";
import "../node_modules/jquery/src/jquery.js";

// fontawesome
import { library } from "@fortawesome/fontawesome-svg-core";
import {
    faPhone,
    faCode,
    faArchive,
    faFlask,
    faSuperscript,
    faEquals,
    faTachometerAlt,
    faLeaf,
    faRuler,
    faSync,
    faClock,
    faDna,
    faLongArrowAltLeft,
    faFileCode,
    faPlug,
    faSitemap,
    faLessThanEqual,
    faBullseye,
    faFileAlt,
    faFileCsv,
    faSearch,
    faStream,
    faCheckCircle,
    faTimesCircle,
    faFileMedicalAlt,
    faTablets,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

library.add({
    faPhone,
    faCode,
    faArchive,
    faFlask,
    faSuperscript,
    faEquals,
    faTachometerAlt,
    faLeaf,
    faRuler,
    faSync,
    faClock,
    faDna,
    faLongArrowAltLeft,
    faFileCode,
    faPlug,
    faSitemap,
    faLessThanEqual,
    faBullseye,
    faFileAlt,
    faFileCsv,
    faSearch,
    faStream,
    faCheckCircle,
    faTimesCircle,
    faFileMedicalAlt,
    faTablets,
});

createApp(App)
    .use(store)
    .use(router)
    .use(List)
    .component("font-awesome-icon", FontAwesomeIcon)
    .mount("#app");
