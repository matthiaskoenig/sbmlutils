<template>
    <a-list class="list-container">
        <toaster
            v-for="sbase in collectSBases"
            v-bind:key="sbase.id + sbase.sbo + sbase.name + sbase.metaId"
            v-bind:sbmlType="sbase.sbmlType"
            v-bind:info="sbase"
            v-bind:visible="Boolean(visibility[sbase.sbmlType])"
        ></toaster>
    </a-list>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import listOfSBMLTypes from "@/data/listOfSBMLTypes";
import allSBML from "@/data/allSBMLMap";
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
        /**
         * Collects and returns SBML objects present in the report and
         * applies search filtering on the response set.
         */
        collectSBases(): Array<Record<string, unknown>> {
            let sbases: Array<Record<string, unknown>> = store.getters.sbases;
            console.log(sbases);
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
