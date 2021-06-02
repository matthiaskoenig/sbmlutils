<template>
    <div class="list-group">
        <sBase
            v-for="sbase in listOfSBases"
            v-bind:key="sbase.sbo"
            v-bind:info="sbase"
        ></sBase>
    </div>
</template>

<script>
import store from "@/store/index";

/* Compartments */
import SBase from "@/components/sbml/SBase";

export default {
    components: {
        sBase: SBase,
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
@import "@/assets/styles/scss/components/sbml/listOf/ListOfSBases.scss";
</style>
