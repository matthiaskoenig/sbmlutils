<template>
    <div id="modelDiv" v-if="sbmlType === 'Model'">
        <model v-bind:info="info"></model>
    </div>

    <div id="portDiv" v-if="sbmlType === 'Port'">
        <port v-bind:info="info"></port>
    </div>

    <div id="compartmentDiv" v-if="sbmlType === 'Compartment'">
        <compartment v-bind:info="info"></compartment>
    </div>

    <div id="speciesDiv" v-if="sbmlType === 'Species'">
        <species v-bind:info="info"></species>
    </div>

    <div id="parameterDiv" v-if="sbmlType === 'Parameter'">
        <parameter v-bind:info="info"></parameter>
    </div>

    <div id="reactionsDiv" v-if="sbmlType === 'Reaction'">
        <reaction v-bind:info="info"></reaction>
    </div>
</template>

<script>
import Model from "@/components/sbml/Model.vue";
import Port from "@/components/sbml/Port.vue";
import Compartment from "@/components/sbml/Compartment.vue";
import Species from "@/components/sbml/Species.vue";
import Parameter from "@/components/sbml/Parameter.vue";
import Reaction from "@/components/sbml/Reaction.vue";

export default {
    props: {
        sbmlType: String,
        info: {},
    },

    components: {
        model: Model,
        port: Port,
        compartment: Compartment,
        species: Species,
        reaction: Reaction,
        parameter: Parameter,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/ComponentSpecificDetails.scss";
</style>
