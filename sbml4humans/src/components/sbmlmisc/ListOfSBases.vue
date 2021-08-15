<template>
    <!-- <PanelMenu :model="items" v-model:expandedKeys="expandedKeys" /> -->

    <strong>Document & Models</strong>
    <ScrollPanel class="basics-container">
        <SBML-toaster
            v-for="component in collectReportBasics"
            :key="component.pk"
            :sbmlType="component.sbmlType"
            :info="component"
            :visible="Boolean(visibility[component.sbmlType])"
        />
    </ScrollPanel>

    <strong>SBases</strong>
    <list-of-tables class="tables-container" />
</template>

<script lang="ts">
import store from "@/store/index";
import icons from "@/data/fontAwesome";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import SBMLToaster from "@/components/layout/SBMLToaster.vue";
import ListOfTables from "@/components/sbmlmisc/ListOfTables.vue";

export default defineComponent({
    components: {
        SBMLToaster,
        ListOfTables,
    },

    data() {
        return {
            selectedCountries: null,
            expandedKeys: {"0": true, "1": true},
            reportBasics: [] as Array<Record<string, unknown>>,
            sbases: [] as Array<Record<string, unknown>>,
        };
    },

    // mounted() {
    //     this.setItems(this.collectReportBasics, this.collectTables);
    // },

    methods: {
        // setItems(
        //     reportBasics: Array<Record<string, unknown>>,
        //     tables: Record<string, Array<string>>
        // ): void {
        //     let basics = [] as Array<Record<string, unknown>>;

        //     for (let i = 0; i < reportBasics.length; i++) {
        //         const component = reportBasics[i];
        //         basics.push(component);
        //     }

        //     this.reportBasics = basics;

        //     let listOfTables = {
        //         key: 1,
        //         label: "SBases",
        //         items: [] as Array<Record<string, unknown>>,
        //     };

        //     let i = 0;
        //     for (const table in tables) {
        //         i++;
        //         listOfTables.items.push({
        //             key: "1_" + i,
        //             label: (table === "Species" ? table : table + "s") + " (" + this.counts[table as string] + ")",
        //             iconString: icons.icons[table as string],
        //         });
        //     }

        //     items.push(listOfTables);

        //     this.items = items;
        // },
    },

    computed: {
        collectReportBasics(): Array<Record<string, unknown>> {
            return store.getters.reportBasics;
        },

        collectTables(): Record<string, Array<string>> {
            let tables: Record<string, Array<string>> = {};

            const componentPKsMap: Record<string, Array<string>> =
                store.getters.componentPKsMap;

            for (let sbmlType in componentPKsMap) {
                if (componentPKsMap[sbmlType].length > 0) {
                    tables[sbmlType] = componentPKsMap[sbmlType];
                }
            }

            return tables;
        },

        /**
         * Reactively returns the visibility of SBML components from Vuex state/localStorage.
         */
        visibility(): Record<string, unknown> {
            return store.state.visibility;
        },

        counts(): Record<string, number> {
            return store.getters.counts;
        },

        /**
         * Reactively returns the searchQuery string from Vuex state/localStorage.
         */
        searchQuery(): string {
            return store.state.searchQuery;
        },
    },

    // watch: {
    //     collectReportBasics() {
    //         this.setItems(this.collectReportBasics, this.collectTables);
    //     },

    //     collectTables() {
    //         this.setItems(this.collectReportBasics, this.collectTables);
    //     },
    // },
});
</script>

<style lang="scss" scoped>
.basics-container {
    padding: 1% 0%;
    max-height: 100%;
    height: fit-content;

    margin-bottom: 2px;
    font-size: 14px !important;
}

.sbase-container {
    padding: 1% 0%;
    height: auto;
    overflow-y: scroll;
}

.tables-container {
    padding: 1% 0%;
    height: auto;

    overflow-y: scroll;
    font-size: 14px !important;
}
</style>
