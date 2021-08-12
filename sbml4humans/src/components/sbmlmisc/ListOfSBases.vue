<template>
    <!--<PanelMenu :model="items" />-->

    <strong>Document & Models</strong>
    <a-list class="basics-container">
        <SBML-toaster
            v-for="component in collectReportBasics"
            :key="component.pk"
            :sbmlType="component.sbmlType"
            :info="component"
            :visible="Boolean(visibility[component.sbmlType])"
        />
    </a-list>

    <div class="mt-3">
        <strong>SBases</strong>
    </div>
    <list-of-tables />
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
        SBMLToaster,
        ListOfTables,
    },

    data() {
        return {
            items: [
                {
                    label: "Document & Models",
                    items: [
                        {
                            label: "New",
                            icon: "pi pi-fw pi-plus",
                            items: [
                                {
                                    label: "Bookmark",
                                    icon: "pi pi-fw pi-bookmark",
                                },
                                {
                                    label: "Video",
                                    icon: "pi pi-fw pi-video",
                                },
                            ],
                        },
                        {
                            label: "Delete",
                            icon: "pi pi-fw pi-trash",
                        },
                        {
                            label: "Export",
                            icon: "pi pi-fw pi-external-link",
                        },
                    ],
                },
                {
                    label: "SBases",
                    items: [
                        {
                            label: "Left",
                            icon: "pi pi-fw pi-align-left",
                        },
                        {
                            label: "Right",
                            icon: "pi pi-fw pi-align-right",
                        },
                        {
                            label: "Center",
                            icon: "pi pi-fw pi-align-center",
                        },
                        {
                            label: "Justify",
                            icon: "pi pi-fw pi-align-justify",
                        },
                    ],
                },
            ],
        };
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
