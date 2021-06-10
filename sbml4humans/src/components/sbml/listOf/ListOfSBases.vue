<template>
    <div class="container">
        <a-list class="list-container">
            <toaster
                v-for="sbase in collectSBases"
                v-bind:key="sbase.id + sbase.sbo + sbase.name + sbase.metaId"
                :sbmlType="sbase.sbmlType"
                :info="sbase"
            ></toaster>
        </a-list>
    </div>
</template>

<script>
import store from "@/store/index";
import TYPES from "@/sbmlComponents";

/* Components */
import SBMLToaster from "@/components/layout/SBMLToaster";

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
            var sbases = [];
            var counts = {
                SBMLDocument: 0,
                Model: 0,
                FunctionDefinitions: 0,
                UnitDefinitions: 0,
                Compartments: 0,
                Species: 0,
                Parameters: 0,
                InitialAssignments: 0,
                Rules: 0,
                Constraints: 0,
                Reactions: 0,
                Objectives: 0,
                Events: 0,
                GeneProducts: 0,
                SubModels: 0,
                Ports: 0,
            };

            // collecting doc
            if (report.doc) {
                counts.SBMLDocument = 1;
                if (this.visibility.SBMLDocument) {
                    sbases.push(report.doc);
                    counts.SBMLDocument = 1;
                }
            }

            if (report.models) {
                sbases.push(...this.assembleSBasesInModels(report.models, counts));
            }

            if (!(this.searchQuery === null || this.searchQuery === "")) {
                sbases = this.filterForSearchResults(sbases, this.searchQuery);
            }

            store.dispatch("updateCounts", counts);
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
            var sbases = [];

            // collecting model
            if (models.model) {
                console.log("found models");
                counts.Model = 1;
                if (this.visibility.Model) {
                    sbases.push(models.model);
                }
            }

            // collecting submodels
            if (models.submodels) {
                console.log("found models");
                counts.SubModels = models.submodels.length;
                if (this.visibility.SubModels) {
                    sbases.push(...models.submodels);
                }
            }

            // collecting ports
            if (models.ports) {
                console.log("found models");
                counts.Ports = models.ports.length;
                if (this.visibility.Ports) {
                    sbases.push(...models.ports);
                }
            }

            // collecting function definitions
            if (models.functionDefinitions) {
                console.log("found models");
                counts.FunctionDefinitions = models.functionDefinitions.length;
                if (this.visibility.FunctionDefinitions) {
                    sbases.push(...models.functionDefinitions);
                }
            }

            // collecting unit definitions
            if (models.unitDefinitions) {
                console.log("found models");
                counts.UnitDefinitions = models.unitDefinitions.length;
                if (this.visibility.UnitDefinitions) {
                    sbases.push(...models.unitDefinitions);
                }
            }

            // collecting compartments
            if (models.compartments) {
                console.log("found models");
                counts.Compartments = models.compartments.length;
                if (this.visibility.Compartments) {
                    sbases.push(...models.compartments);
                }
            }

            // collecting species
            if (models.species) {
                console.log("found models");
                counts.Species = models.species.length;
                if (this.visibility.Species) {
                    sbases.push(...models.species);
                }
            }

            // collecting parameters
            if (models.parameters) {
                console.log("found models");
                counts.Parameters = models.parameters.length;
                if (this.visibility.Parameters) {
                    sbases.push(...models.parameters);
                }
            }

            // collecting intial assignments
            if (models.initialAssignments) {
                console.log("found models");
                counts.InitialAssignments = models.initialAssignments.length;
                if (this.visibility.InitialAssignments) {
                    sbases.push(...models.initialAssignments);
                }
            }

            // collecting rules
            if (models.rules) {
                console.log("found models");
                counts.Rules = models.rules.length;
                if (this.visibility.Rules) {
                    sbases.push(...models.rules);
                }
            }

            // collecting contraints
            if (models.contraints) {
                console.log("found models");
                counts.Constraints = models.constraints.length;
                if (this.visibility.Constraints) {
                    sbases.push(...models.constraints);
                }
            }

            // collecting reactions
            if (models.reactions) {
                console.log("found models");
                counts.Reactions = models.reactions.length;
                if (this.visibility.Reactions) {
                    sbases.push(...models.reactions);
                }
            }

            // collecting objectives
            if (models.objectives) {
                console.log("found models");
                counts.Objectives = models.objectives.length;
                if (this.visibility.Objectives) {
                    sbases.push(...models.objectives);
                }
            }

            // collecting events
            if (models.events) {
                console.log("found models");
                counts.Events = models.events.length;
                if (this.visibility.Events) {
                    sbases.push(...models.events);
                }
            }

            // collecting gene products
            if (models.geneProducts) {
                console.log("found models");
                counts.GeneProducts = models.geneProducts.length;
                if (this.visibility.GeneProducts) {
                    sbases.push(...models.geneProducts);
                }
            }

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
