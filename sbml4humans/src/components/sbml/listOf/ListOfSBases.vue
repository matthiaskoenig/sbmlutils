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

/* Components */
import SBMLToaster from "@/components/layout/SBMLToaster.vue";

export default {
    components: {
        toaster: SBMLToaster,
    },

    data(): Record<string, unknown> {
        return {
            listOfSBases: [TYPES.SBase],
        };
    },

    computed: {
        collectSBases(): Array<Record<string, unknown>> {
            const report = store.state.jsonReport;
            let sbases = this.assembleSBasesInModels(report);

            if (!(this.searchQuery === null || this.searchQuery === "")) {
                sbases = this.filterForSearchResults(sbases, this.searchQuery);
            }

            return sbases;
        },

        visibility(): Record<string, unknown> {
            return store.state.visibility;
        },

        searchQuery(): string {
            return store.state.searchQuery;
        },
    },

    methods: {
        assembleSBasesInModels(
            report: Record<string, Record<string, unknown>> = TYPES.Report
        ): Array<Record<string, unknown>> {
            if (report === null) {
                return [];
            }

            let sbases: Array<Record<string, unknown>> = [];
            let counts: Record<string, number> = {
                SBMLDocument: 0,
                SubModel: 0,
                Port: 0,
                Model: 0,
                FunctionDefinition: 0,
                UnitDefinition: 0,
                Compartment: 0,
                Species: 0,
                Reaction: 0,
                Parameter: 0,
                InitialAssignment: 0,
                AssignmentRule: 0,
                RateRule: 0,
                Objective: 0,
                Constraint: 0,
                Event: 0,
                GeneProduct: 0,
            };
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

        filterForSearchResults(
            sbases: Array<Record<string, unknown>> = [TYPES.SBase],
            searchQuery = ""
        ): Array<Record<string, unknown>> {
            return sbases.filter((sbase) => {
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
        },
    },

    mounted(): void {
        this.listOfSBases = this.collectSBases;
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/listOf/ListOf.scss";
</style>
