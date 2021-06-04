<template>
    <div class="container">
        <h5 class="header-pill">List of Compartments</h5>
        <a-list bordered class="list-container">
            <toaster
                v-for="compt in collectCompartments"
                v-bind:key="compt.id"
                v-bind:sid="compt.id"
                v-bind:name="compt.name"
                v-bind:sbmlType="compt.sbaseType"
                v-bind:info="compt"
            ></toaster>
        </a-list>
    </div>
</template>

<script>
import store from "@/store/index";

/* Compartments */
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
        collectCompartments() {
            return store.state.compartments;
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
