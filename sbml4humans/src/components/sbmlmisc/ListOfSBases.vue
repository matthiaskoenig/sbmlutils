<template>
    <strong>Document & Models</strong>
    <ScrollPanel class="basics-container">
        <SBML-toaster
            v-for="component in collectReportBasics"
            :key="component.pk"
            :sbmlType="component.sbmlType"
            :info="component"
        />
    </ScrollPanel>

    <strong>SBases</strong>
    <list-of-tables class="tables-container" />
</template>

<script lang="ts">
import store from "@/store/index";
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
            expandedKeys: { "0": true, "1": true },
            reportBasics: [] as Array<Record<string, unknown>>,
            sbases: [] as Array<Record<string, unknown>>,
        };
    },

    computed: {
        collectReportBasics(): Array<Record<string, unknown>> {
            return store.getters.reportBasics;
        },

        collectTables(): Record<string, Array<string>> {
            let tables: Record<string, Array<string>> = {};

            const componentPKsMap: Record<string, Array<string>> = store.getters
                .componentPKsMap;

            for (let sbmlType in componentPKsMap) {
                if (componentPKsMap[sbmlType].length > 0) {
                    tables[sbmlType] = componentPKsMap[sbmlType];
                }
            }

            return tables;
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
