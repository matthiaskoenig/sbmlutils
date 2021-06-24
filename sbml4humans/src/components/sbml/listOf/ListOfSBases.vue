<template>
    <div class="container">
        <a-list class="list-container">
            <toaster
                v-for="sbase in collectSBases"
                v-bind:key="sbase.id + sbase.sbo + sbase.name + sbase.metaId"
                :sbmlType="sbase.sbmlType"
                :info="sbase"
                :visible="Boolean(visibility[sbase.sbmlType])"
            ></toaster>
        </a-list>
    </div>
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
         * Collects the SBML Document and all model definitions from the backend API
         * response. It then collects other SBML objects in these definitions. Also
         * updates the count of SBML components and initializes global component maps.
         * @param report The generated SBML report sent in the API response.
         */
        assembleSBasesInReport(
            report: Record<string, unknown>
        ): Array<Record<string, unknown>> {
            if (report === null) {
                return [];
            }

            let sbases: Array<Record<string, unknown>> = [];
            let counts: Record<string, number> = store.state.counts;
            let allObjectsMap: Record<string, unknown> = {};
            let componentPKsMap: Record<string, Array<string>> = allSBML.componentsMap;

            // collecting doc
            if (report.doc) {
                counts["SBMLDocument"] = 1;
                sbases.push(report.doc as Record<string, unknown>);
                allObjectsMap[(report.doc as Record<string, unknown>).pk as string] =
                    report.doc;
            }

            let model: Record<string, unknown> = report.model as Record<
                string,
                unknown
            >;

            if (model) {
                counts["Model"] = 1;
                sbases.push(model);

                componentPKsMap["Model"] = [];

                const pk = model.pk as string;
                allObjectsMap[pk] = model;
                componentPKsMap["Model"].push(pk);

                // collecting all other components
                sbases.push(
                    ...this.collectSBasesInModel(
                        model,
                        counts,
                        allObjectsMap,
                        componentPKsMap
                    )
                );
            }

            store.dispatch("updateCounts", counts);
            store.dispatch("updateAllObjectsMap", allObjectsMap);
            store.dispatch("updateComponentPKsMap", componentPKsMap);

            return sbases;
        },

        /**
         * Collects SBML objects inside a particular model definition.
         * @param model The SBML model
         * @param counts Global counts map
         * @param allObjectsMap Global map for all SBML objects
         * @param componentPKsMap Global map for component-wise SBML objects
         */
        collectSBasesInModel(
            model: Record<string, unknown>,
            counts: Record<string, number>,
            allObjectsMap: Record<string, unknown>,
            componentPKsMap: Record<string, Array<unknown>>
        ): Array<Record<string, unknown>> {
            let sbasesInModel: Array<Record<string, unknown>> = [];

            for (let i = 0; i < listOfSBMLTypes.listOfSBMLTypes.length; i++) {
                const sbmlType = listOfSBMLTypes.listOfSBMLTypes[i];

                // camel case keys, present in the API response E.g. unitDefinitions, compartments
                let key: string = sbmlType.charAt(0).toLowerCase() + sbmlType.slice(1);
                if (sbmlType != "Species") {
                    key = key + "s";
                }

                if (model[key]) {
                    const component: Array<Record<string, unknown>> = model[
                        key
                    ] as Array<Record<string, unknown>>;

                    componentPKsMap[sbmlType] = [];

                    counts[sbmlType] = component.length as number;
                    component.forEach((sbase) => {
                        sbasesInModel.push(sbase);

                        const pk = sbase.pk as string;
                        allObjectsMap[pk] = sbase;
                        componentPKsMap[sbmlType].push(pk);
                    });
                }
            }

            return sbasesInModel;
        },

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
            const report = store.state.jsonReport;
            let sbases: Array<Record<string, unknown>> =
                this.assembleSBasesInReport(report);

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
