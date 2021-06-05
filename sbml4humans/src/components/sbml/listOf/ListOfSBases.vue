<template>
    <div class="container">
        <a-list bordered class="list-container">
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
        };
    },

    computed: {
        collectSBases() {
            const report = store.state.jsonReport;
            var sbases = [];

            // collecting doc
            if (report.doc) {
                console.log("found doc");
                sbases.push(report.doc);
            }

            if (report.models) {
                sbases.push(...this.assembleSBasesInModels(report.models));
            }

            return sbases;
        },
    },

    methods: {
        assembleSBasesInModels(models = TYPES.Models) {
            var sbases = [];

            // collecting model
            if (models.model) {
                console.log("found model");
                sbases.push(models.model);
            }

            // collecting submodels
            if (models.submodels) {
                console.log("found submodels");
                sbases.push(...models.submodels);
            }

            // collecting ports
            if (models.ports) {
                console.log("found ports");
                sbases.push(...models.ports);
            }

            // collecting function definitions
            if (models.functionDefinitions) {
                console.log("found func defs");
                sbases.push(...models.functionDefinitions);
            }

            // collecting unit definitions
            if (models.unitDefinitions) {
                console.log("found unit defs");
                sbases.push(...models.unitDefinitions);
            }

            // collecting compartments
            if (models.compartments) {
                console.log("found compartments");
                sbases.push(...models.compartments);
            }

            // collecting species
            if (models.species) {
                console.log("found species");
                sbases.push(...models.species);
            }

            // collecting parameters
            if (models.parameters) {
                console.log("found parameters");
                sbases.push(...models.parameters);
            }

            // collecting intial assignments
            if (models.initialAssignments) {
                console.log("found initial assignments");
                sbases.push(...models.initialAssignments);
            }

            // collecting rules
            if (models.rules) {
                console.log("found rules");
                sbases.push(...models.rules);
            }

            // collecting contraints
            if (models.contraints) {
                console.log("found contraints");
                sbases.push(...models.constraints);
            }

            // collecting reactions
            if (models.reactions) {
                console.log("found reactions");
                sbases.push(...models.reactions);
            }

            // collecting objectives
            if (models.objectives) {
                console.log("found objectives");
                sbases.push(...models.objectives);
            }

            // collecting events
            if (models.events) {
                console.log("found events");
                sbases.push(...models.events);
            }

            // collecting gene products
            if (models.geneProducts) {
                console.log("found gene products");
                sbases.push(...models.geneProducts);
            }

            return sbases;
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
