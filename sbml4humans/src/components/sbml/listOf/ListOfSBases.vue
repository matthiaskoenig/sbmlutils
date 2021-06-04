<template>
    <div class="container">
        <h5 class="header-pill">List of SBases</h5>
        <a-list bordered class="list-container">
            <toaster
                v-for="sbase in listOfSBases"
                v-bind:key="sbase.id"
                v-bind:sid="sbase.id"
                v-bind:name="sbase.name"
                v-bind:sbmlType="sbase.sbaseType"
                v-bind:info="sbase"
            ></toaster>
        </a-list>
    </div>
</template>

<script>
import store from "@/store/index";

/* Components */
import SBMLToaster from "@/components/SBMLToaster";

export default {
    components: {
        toaster: SBMLToaster,
    },

    data() {
        return {
            listOfSBases: [],
        };
    },

    computed: {
        collectSBases() {
            const report = store.state.jsonReport.report;
            var listOfSBases = [];

            // collecting doc
            if (report.doc) {
                console.log("found doc");
                var doc = report.doc;
                listOfSBases.push(doc);
            }

            const sbmlInfo = report.models;
            // collecting compartments
            if (sbmlInfo.compartments) {
                console.log("found compartments in sbases");
                var compartments = sbmlInfo.compartments;
                listOfSBases.push(...compartments);
                console.log(compartments);
            }

            // collecting species
            if (sbmlInfo.species) {
                console.log("found species");
                var species = sbmlInfo.species;
                listOfSBases.push(...species);
            }

            return listOfSBases;
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
