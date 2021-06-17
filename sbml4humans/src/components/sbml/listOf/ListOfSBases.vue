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
import TYPES from "@/sbmlComponents";
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
         * Collects all SBML components from the backend API response and classifies
         * them on the basis of SBML Type. Also updates the count of SBML components
         * and initializes global component maps.
         * @param report The generated SBML report sent in the API response.
         */
        assembleSBasesInModels(
            report: Record<string, Record<string, unknown>> = TYPES.Report
        ): Array<Record<string, unknown>> {
            if (report === null) {
                return [];
            }

            let sbases: Array<Record<string, unknown>> = [];
            let counts: Record<string, number> = store.state.counts;
            let allObjectsMap: Record<string, unknown> = {};
            let componentPKsMap: Record<string, Array<unknown>> = allSBML.componentsMap;

            // collecting doc
            if (report.doc) {
                counts["SBMLDocument"] = 1;
                sbases.push(report.doc as Record<string, unknown>);

                allObjectsMap[report.doc.pk as string] = report.doc;
            }

            const models: Record<string, unknown> = report.models;

            // collecting model
            if (models.model) {
                const model = models.model as Record<string, unknown>;

                counts["Model"] = 1;
                sbases.push(model);

                const pk = model.pk as string;
                allObjectsMap[pk] = model;
                componentPKsMap["Model"].push(pk);
            }

            // collecting species
            if (models.species) {
                const species = models.species as Array<Record<string, unknown>>;

                counts["Species"] = species.length as number;
                species.forEach((sbase) => {
                    sbases.push(sbase);

                    const pk = sbase.pk as string;
                    allObjectsMap[pk] = sbase;
                    componentPKsMap["Species"].push(pk);
                });
            }

            // collecting all other components
            for (let i = 0; i < listOfSBMLTypes.listOfSBMLTypes.length; i++) {
                const sbmlType = listOfSBMLTypes.listOfSBMLTypes[i];

                // camel case keys, present in the API response E.g. unitDefinitions, compartments
                let key: string =
                    sbmlType.charAt(0).toLowerCase() + sbmlType.slice(1) + "s";

                if (models[key]) {
                    const component: Array<Record<string, unknown>> = models[
                        key
                    ] as Array<Record<string, unknown>>;

                    counts[sbmlType] = component.length as number;
                    component.forEach((sbase) => {
                        sbases.push(sbase);

                        const pk = sbase.pk as string;
                        allObjectsMap[pk] = sbase;
                        componentPKsMap[sbmlType].push(pk);
                    });
                }
            }

            store.dispatch("updateCounts", counts);
            store.dispatch("updateAllObjectsMap", allObjectsMap);
            store.dispatch("updateComponentPKsMap", componentPKsMap);

            return sbases;
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
            console.log("henlo");

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

            console.log("henlo");
            searchedSbases.forEach((sbase) => {
                const pk = sbase.pk as string;
                searchedSet.add(pk);
                console.log("searched " + pk);
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
                this.assembleSBasesInModels(report);

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
