import { createApp } from "vue";
import App from "./App.vue";
import "./registerServiceWorker";
import router from "./router";
import store from "./store";

// bootstrap FIXME: remove
import "../node_modules/bootstrap/dist/css/bootstrap.css";
import "../node_modules/bootstrap/dist/js/bootstrap.bundle.js";

// PrimeVue UI package
import PrimeVue from "primevue/config";
import Badge from "primevue/badge";
import ProgressSpinner from "primevue/progressspinner";
import ScrollPanel from "primevue/scrollpanel";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Dropdown from "primevue/dropdown";
import Button from "primevue/button";
import Slider from "primevue/slider";
import InputText from "primevue/inputtext";
import PanelMenu from "primevue/panelmenu";
import Accordion from "primevue/accordion";
import AccordionTab from "primevue/accordiontab";

import "primevue/resources/themes/saga-blue/theme.css"; //theme
import "primevue/resources/primevue.min.css"; //core css
import "primeicons/primeicons.css"; //icons
import { FilterMatchMode, FilterOperator } from "primevue/api";

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
    faArrowLeft,
    faArrowRight
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
    faArrowLeft,
    faArrowRight,
});

createApp(App)
    .use(store)
    .use(router)
    .use(PrimeVue)
    .component("font-awesome-icon", FontAwesomeIcon)
    .component("Badge", Badge)
    .component("ProgressSpinner", ProgressSpinner)
    .component("ScrollPanel", ScrollPanel)
    .component("DataTable", DataTable)
    .component("Column", Column)
    .component("Dropdown", Dropdown)
    .component("Button", Button)
    .component("Slider", Slider)
    .component("FilterMatchMode", FilterMatchMode)
    .component("FilterOperator", FilterOperator)
    .component("InputText", InputText)
    .component("PanelMenu", PanelMenu)
    .component("Accordion", Accordion)
    .component("AccordionTab", AccordionTab)
    .mount("#app");
