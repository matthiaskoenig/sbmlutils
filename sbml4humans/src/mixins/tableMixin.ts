import store from "@/store/index";
import icons from "@/data/fontAwesome";
import colorScheme from "@/data/colorScheme";

import { FilterMatchMode, FilterOperator } from "primevue/api";

import Katex from "@/components/layout/Katex.vue";
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

const tableMixin = (sbmlType: string): Record<string, unknown> => ({
    name: "tableMixin",
    components: {
        Katex,
        BooleanSymbol,
    },

    data() {
        return {
            filters: {
                global: { value: null, matchMode: FilterMatchMode.CONTAINS },
                searchUtilField: {
                    operator: FilterOperator.AND,
                    constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
                },
            },
        };
    },

    computed: {
        color(): string {
            return colorScheme.componentColor[sbmlType];
        },

        icon(): string {
            return icons.icons[sbmlType];
        },
        count(): number {
            return store.state.searchedSBasesCounts[sbmlType];
        },
        header(): string {
            if (sbmlType === "Species") {
                return "Species (" + store.state.searchedSBasesCounts[sbmlType] + ")";
            } else {
                return (
                    sbmlType + " (" + store.state.searchedSBasesCounts[sbmlType] + ")"
                );
            }
        },
    },

    methods: {
        openComponent(pk: string): void {
            //console.log(pk);
            store.dispatch("pushToHistoryStack", pk);
        },
    },
});

export default tableMixin;
