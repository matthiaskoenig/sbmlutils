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

<script>
import store from "@/store/index";
import TYPES from "@/sbmlComponents";

/* Components */
import SBMLToaster from "@/components/layout/SBMLToaster";
import listOfSBMLTypes from '@/data/listOfSBMLTypes';

export default {
    components: {
        toaster: SBMLToaster,
    },

    data() {
        return {
            listOfSBases: [TYPES.SBase],
        };
    },

    computed: {
        collectSBases() {
            const report = store.state.jsonReport;
            let sbases = [];
            let counts = {
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

            // collecting doc
            if (report.doc) {
                counts.SBMLDocument = 1;
                //this.visibility.SBMLDocument = true;
                sbases.push(report.doc);
                counts["SBMLDocument"] = 1;
            }

            if (report.models) {
                sbases.push(...this.assembleSBasesInModels(report.models, counts));
            }

            if (!(this.searchQuery === null || this.searchQuery === "")) {
                sbases = this.filterForSearchResults(sbases, this.searchQuery);
            }

            return sbases;
        },

        visibility() {
            return store.state.visibility;
        },

        searchQuery() {
            return store.state.searchQuery;
        },
    },

    methods: {
        assembleSBasesInModels(models = TYPES.Models, counts) {
            let sbases = [];

            if (models.model) {
                counts["Model"] = 1;
                sbases.push(models.model);
            }

            if (models.species) {
                counts["Species"] = models.species.length;
                sbases.push(...models.species);
            }

            for (let i = 0; i < listOfSBMLTypes.listOfSBMLTypes.length; i++) {
                const sbmlType = listOfSBMLTypes.listOfSBMLTypes[i];

                // camel case keys, present in the API response E.g. unitDefinitions, compartments
                let key = sbmlType.charAt(0).toLowerCase() + sbmlType.slice(1) + "s";

                if (models[key]) {
                    console.log("found " + sbmlType);
                    counts[sbmlType] = models[key].length;
                    sbases.push(...models[key]);
                }
            }

            store.dispatch("updateCounts", counts);

            return sbases;
        },

        filterForSearchResults(sbases = [TYPES.SBase], searchQuery = "") {
            return sbases.filter((sbase) => {
                return searchQuery
                    .toLowerCase()
                    .split(" ")
                    .every((attr) =>
                        (sbase.name + sbase.id + sbase.metaId + sbase.sbo)
                            .toString()
                            .toLowerCase()
                            .includes(attr)
                    );
            });
        },
    },

    mounted() {
        this.listOfSBases = this.collectSBases;
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/listOf/ListOf.scss";
</style>
