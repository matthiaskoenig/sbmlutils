<template>
    <div id="compartmentDiv" v-if="sbmlType === 'Compartment'">
        <compartment v-bind:info="info"></compartment>
    </div>

    <div id="speciesDiv" v-if="sbmlType === 'Species'">
        <species v-bind:info="info"></species>
    </div>
</template>

<script>
import Compartment from "@/components/sbml/Compartment.vue";
import Species from "@/components/sbml/Species.vue";

export default {
    props: {
        sbmlType: String,
        info: {},
    },

    components: {
        compartment: Compartment,
        species: Species,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/ComponentSpecificDetails.scss";
</style>
