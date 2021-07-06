<template>
    <a-list class="table-container">
        <toaster
            v-for="(listOfPKs, sbmlType) in collectTables"
            v-bind:key="sbmlType"
            v-bind:sbmlType="sbmlType"
            v-bind:listOfPKs="listOfPKs"
            v-bind:visible="Boolean(visibility[sbmlType]) && listOfPKs.length > 0"
        ></toaster>
    </a-list>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import TableToaster from "@/components/layout/TableToaster.vue";

export default defineComponent({
    components: {
        toaster: TableToaster,
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
        collectTables(): Record<string, Array<string>> {
            return store.getters.tables;
        },

        /**
         * Reactively returns the visibility of SBML components from Vuex state/localStorage.
         */
        visibility(): Record<string, unknown> {
            return store.state.visibility;
        },
    },
});
</script>

<style lang="scss" scoped>
.basics-container{
    padding: 1% 0%;
    max-height: 100%;
    height: fit-content;

    margin-bottom: 2px;
}

.sbase-container{
    padding: 1% 0%;
    height: auto;

    overflow-y: scroll;
}

.table-container{
    padding: 1% 0%;
    height: auto;

    overflow-y: scroll;
}
</style>
