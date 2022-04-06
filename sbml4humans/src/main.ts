// core
import { createApp } from "vue";
import App from "./App.vue";
// import "./registerServiceWorker";
import router from "./router";
import store from "./store";

// google analytics
import VueGtag from "vue-gtag-next";

// PrimeVue UI package
import "primevue/resources/themes/bootstrap4-light-blue/theme.css";
import "primevue/resources/primevue.min.css";
import "primeicons/primeicons.css";
import "primeflex/primeflex.css";
import { FilterMatchMode, FilterOperator } from "primevue/api";

import PrimeVue from "primevue/config";
import Badge from "primevue/badge";
import ProgressSpinner from "primevue/progressspinner";
import ProgressBar from "primevue/progressbar";
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import Dropdown from "primevue/dropdown";
import Button from "primevue/button";
import Slider from "primevue/slider";
import InputText from "primevue/inputtext";
import Menubar from "primevue/menubar";
import PanelMenu from "primevue/panelmenu";
import FileUpload from "primevue/fileupload";
import Card from "primevue/card";
import Tag from "primevue/tag";
import OrderList from "primevue/orderlist";
import ScrollPanel from "primevue/scrollpanel";
import DataView from "primevue/dataview";
import TabView from "primevue/tabview";
import TabPanel from "primevue/tabpanel";
import Textarea from "primevue/textarea";
import Panel from "primevue/panel";
import Splitter from "primevue/splitter";
import SplitterPanel from "primevue/splitterpanel";
import Dialog from "primevue/dialog";
import Tree from "primevue/tree";

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
    faArrowRight,
    faSquare,
    faCheckSquare
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import Checkbox from "primevue/checkbox";

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
    faSquare,
    faCheckSquare
});

// app initialization
const app = createApp(App)
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
    .component("Menubar", Menubar)
    .component("PanelMenu", PanelMenu)
    .component("FileUpload", FileUpload)
    .component("Card", Card)
    .component("Tag", Tag)
    .component("OrderList", OrderList)
    .component("DataView", DataView)
    .component("TabView", TabView)
    .component("TabPanel", TabPanel)
    .component("Textarea", Textarea)
    .component("Panel", Panel)
    .component("Splitter", Splitter)
    .component("SplitterPanel", SplitterPanel)
    .component("Dialog", Dialog)
    .component("ProgressBar", ProgressBar)
    .component("Checkbox", Checkbox)
    .component("Tree", Tree);


app.use(VueGtag, {
    property: {
        id: "G-TZ6E25RS0Q",
    },
});
app.mount("#app");
