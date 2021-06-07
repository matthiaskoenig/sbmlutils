<template>
    <div class="container">
        <a-list class="list-container">
            <toaster
                v-for="sbase in collectSBases"
                v-bind:key="sbase.id"
                v-bind:sid="sbase.id"
                v-bind:name="sbase.name"
                v-bind:sbmlType="sbase.sbmlType"
                v-bind:info="sbase"
            ></toaster>
        </a-list>
    </div>
</template>

<script>
import store from "@/store/index";
import TYPES from "@/sbmlComponents";

/* Components */
import SBMLToaster from "@/components/SBMLToaster";

export default {
    components: {
        toaster: SBMLToaster,
    },

    data() {
        return {
            listOfSBases: [TYPES.SBase],

            visibility: {
                SBMLDocument: true,
                Model: true,
                FunctionDefinitions: true,
                UnitDefinitions: true,
                Compartments: true,
                Species: true,
                Parameters: true,
                InitialAssignments: true,
                Rules: true,
                Constraints: true,
                Reactions: true,
                Objectives: true,
                Events: true,
                GeneProducts: true,
                SubModels: true,
                Ports: true,
            },
        };
    },

    computed: {
        collectSBases() {
            const report = store.state.jsonReport;
            var sbases = [];

            // collecting doc
            if (report.doc) {
                console.log("found doc");
                if (this.visibility.SBMLDocument) {
                    sbases.push(report.doc);
                }
            }

            if (report.models) {
                sbases.push(...this.assembleSBasesInModels(report.models));
            }

            return sbases;
        },

        visibilityAlteredAgain() {
            return store.state.visibilityAltered.alteredAgain;
        },
    },

    methods: {
        assembleSBasesInModels(models = TYPES.Models) {
            var sbases = [];

            // collecting model
            if (models.model && this.visibility.Model) {
                console.log("found model");
                sbases.push(models.model);
            }

            // collecting submodels
            if (models.submodels && this.visibility.SubModels) {
                console.log("found submodels");
                sbases.push(...models.submodels);
            }

            // collecting ports
            if (models.ports && this.visibility.Ports) {
                console.log("found ports");
                sbases.push(...models.ports);
            }

            // collecting function definitions
            if (models.functionDefinitions && this.visibility.FunctionDefinitions) {
                console.log("found func defs");
                sbases.push(...models.functionDefinitions);
            }

            // collecting unit definitions
            if (models.unitDefinitions && this.visibility.UnitDefinitions) {
                console.log("found unit defs");
                sbases.push(...models.unitDefinitions);
            }

            // collecting compartments
            if (models.compartments && this.visibility.Compartments) {
                console.log("found compartments");
                sbases.push(...models.compartments);
            }

            // collecting species
            if (models.species && this.visibility.Species) {
                console.log("found species");
                sbases.push(...models.species);
            }

            // collecting parameters
            if (models.parameters && this.visibility.Parameters) {
                console.log("found parameters");
                sbases.push(...models.parameters);
            }

            // collecting intial assignments
            if (models.initialAssignments && this.visibility.InitialAssignments) {
                console.log("found initial assignments");
                sbases.push(...models.initialAssignments);
            }

            // collecting rules
            if (models.rules && this.visibility.Rules) {
                console.log("found rules");
                sbases.push(...models.rules);
            }

            // collecting contraints
            if (models.contraints && this.visibility.Constraints) {
                console.log("found contraints");
                sbases.push(...models.constraints);
            }

            // collecting reactions
            if (models.reactions && this.visibility.Reactions) {
                console.log("found reactions");
                sbases.push(...models.reactions);
            }

            // collecting objectives
            if (models.objectives && this.visibility.Objectives) {
                console.log("found objectives");
                sbases.push(...models.objectives);
            }

            // collecting events
            if (models.events && this.visibility.Events) {
                console.log("found events");
                sbases.push(...models.events);
            }

            // collecting gene products
            if (models.geneProducts && this.visibility.GeneProducts) {
                console.log("found gene products");
                sbases.push(...models.geneProducts);
            }

            return sbases;
        },
    },

    mounted() {
        this.listOfSBases = this.collectSBases;
    },

    watch: {
        visibilityAlteredAgain() {
            this.visibility[store.state.visibilityAltered.alteredFor] =
                !this.visibility[store.state.visibilityAltered.alteredFor];
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/listOf/ListOf.scss";
</style>
