<template>
    <span>Models</span>
    <a-list class="basics-container">
        <toaster
            v-for="component in collectReportBasics"
            v-bind:key="component.pk"
            v-bind:sbmlType="component.sbmlType"
            v-bind:info="component"
            v-bind:visible="Boolean(visibility[component.sbmlType])"
            v-bind:isModel="Boolean(true)"
        ></toaster>
    </a-list>

    <span class="mt-2">SBML Components</span>
    <a-list class="sbase-container">
        <toaster
            v-for="sbase in collectSBases"
            v-bind:key="sbase.pk"
            v-bind:sbmlType="sbase.sbmlType"
            v-bind:info="sbase"
            v-bind:visible="Boolean(visibility[sbase.sbmlType])"
        ></toaster>
    </a-list>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import SBMLToaster from "@/components/layout/SBMLToaster.vue";

export default defineComponent({
    components: {
        toaster: SBMLToaster,
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
@import "@/assets/styles/scss/components/sbml/listOf/ListOf.scss";
</style>
