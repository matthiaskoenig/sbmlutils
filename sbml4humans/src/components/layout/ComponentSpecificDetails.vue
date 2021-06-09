<template>
    <div id="compartmentDiv" v-if="sbmlType === 'Compartment'">
        <compartment v-bind:info="info"></compartment>
    </div>

    <div id="speciesDiv" v-if="sbmlType === 'Species'">
        <species v-bind:info="info"></species>
    </div>

    <div id="reactionsDiv" v-if="sbmlType === 'Reaction'">
        <reaction v-bind:info="info"></reaction>
    </div>
</template>

<script>
import Compartment from "@/components/sbml/Compartment.vue";
import Species from "@/components/sbml/Species.vue";
import Reaction from "@/components/sbml/Reaction.vue";

export default {
    props: {
        sbmlType: String,
        info: {},
    },

    components: {
        compartment: Compartment,
        species: Species,
        reaction: Reaction,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/ComponentSpecificDetails.scss";
</style>
