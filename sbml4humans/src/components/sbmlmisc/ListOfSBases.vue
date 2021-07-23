<template>
    <span>Document and Models</span>
    <a-list class="basics-container">
        <toaster
            v-for="component in collectReportBasics"
            :key="component.pk"
            :sbmlType="component.sbmlType"
            :info="component"
            :visible="Boolean(visibility[component.sbmlType])"
        ></toaster>
    </a-list>

    <span class="mt-2">List of Components</span>
    <list-of-tables></list-of-tables>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import SBMLToaster from "@/components/layout/SBMLToaster.vue";
import ListOfTables from "@/components/sbmlmisc/ListOfTables.vue";

export default defineComponent({
    components: {
        toaster: SBMLToaster,
        "list-of-tables": ListOfTables,
    },

    methods: {
        /**
         * Filters SBML objects on the basis of the search query.
         * @param sbases Array of SBML objects to filter.
         * @param searchQuery The search query to look for in the SBML objects' data
         */
        filterForSearchResults(
            sbases: Array<Record<string, unknown>> = [TYPES.SBase],
            searchQuery = ""
        ): Array<Record<string, unknown>> {
            let searchedSet: Set<string> = new Set();

            let searchedSbases = sbases.filter((sbase) => {
                return searchQuery
                    .toLowerCase()
                    .split(" ")
                    .every((attr) =>
                        (
                            (sbase.name as string) +
                            (sbase.id as string) +
                            (sbase.metaId as string) +
                            (sbase.sbo as string)
                        )
                            .toString()
                            .toLowerCase()
                            .includes(attr)
                    );
            });

            searchedSbases.forEach((sbase) => {
                const pk = sbase.pk as string;
                searchedSet.add(pk);
            });

            store.dispatch("updateSearchedSBasesPKs", searchedSet);

            return searchedSbases;
        },
    },

    computed: {
        collectReportBasics(): Array<Record<string, unknown>> {
            return store.getters.reportBasics;
        },

        /**
         * Collects and returns SBML objects present in the report and
         * applies search filtering on the response set.
         */
        collectSBases(): Array<Record<string, unknown>> {
            let sbases: Array<Record<string, unknown>> = store.getters.sbases;
            sbases = this.filterForSearchResults(sbases, this.searchQuery);
            return sbases;
        },

        /**
         * Reactively returns the visibility of SBML components from Vuex state/localStorage.
         */
        visibility(): Record<string, unknown> {
            return store.state.visibility;
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
}

.sbase-container {
    padding: 1% 0%;
    height: auto;
    overflow-y: scroll;
}

.table-container {
    padding: 1% 0%;
    height: auto;

    overflow-y: scroll;
}
</style>
