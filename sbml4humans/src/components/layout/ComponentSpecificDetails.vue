<template>
    <div id="modelDiv" v-if="sbmlType === 'Model'">
        <model v-bind:info="info"></model>
    </div>

    <div id="portDiv" v-if="sbmlType === 'Port'">
        <port v-bind:info="info"></port>
    </div>

    <div id="functionDefinitionDiv" v-if="sbmlType === 'Function Definition'">
        <function-definition v-bind:info="info"></function-definition>
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

    <div id="reactionDiv" v-if="sbmlType === 'Reaction'">
        <reaction v-bind:info="info"></reaction>
    </div>

    <div id="assignmentRuleDiv" v-if="sbmlType === 'AssignmentRule'">
        <assignment-rule v-bind:info="info"></assignment-rule>
    </div>

    <div id="rateRuleDiv" v-if="sbmlType === 'RateRule'">
        <rate-rule v-bind:info="info"></rate-rule>
    </div>

    <div id="algebraicRuleDiv" v-if="sbmlType === 'AlgebraicRule'">
        <algebraic-rule v-bind:info="info"></algebraic-rule>
    </div>

    <div id="constraintDiv" v-if="sbmlType === 'Constraint'">
        <constraint v-bind:info="info"></constraint>
    </div>

    <div id="eventDiv" v-if="sbmlType === 'Event'">
        <event v-bind:info="info"></event>
    </div>

    <div id="objectiveDiv" v-if="sbmlType === 'Objective'">
        <objective v-bind:info="info"></objective>
    </div>

    <div id="geneProductDiv" v-if="sbmlType === 'GeneProduct'">
        <gene-product v-bind:info="info"></gene-product>
    </div>
</template>

<script lang="ts">
import TYPES from "@/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import Model from "@/components/sbml/Model.vue";
import Port from "@/components/sbml/Port.vue";
import FunctionDefinition from "@/components/sbml/FunctionDefinition.vue";
import Compartment from "@/components/sbml/Compartment.vue";
import Species from "@/components/sbml/Species.vue";
import Parameter from "@/components/sbml/Parameter.vue";
import Reaction from "@/components/sbml/Reaction.vue";
import AssignmentRule from "@/components/sbml/AssignmentRule.vue";
import RateRule from "@/components/sbml/RateRule.vue";
import AlgebraicRule from "@/components/sbml/AlgebraicRule.vue";
import Constraint from "@/components/sbml/Constraint.vue";
import Event from "@/components/sbml/Event.vue";
import Objective from "@/components/sbml/Objective.vue";
import GeneProduct from "@/components/sbml/GeneProduct.vue";

/*
 * Component to inject a specific SBML component as required by in the parent component.
 */
export default defineComponent({
    props: {
        sbmlType: {
            type: String,
            default: "SBMLDocument",
        },
        info: {
            type: Object,
            default: TYPES.SBMLDocument,
        },
    },

    components: {
        model: Model,
        port: Port,
        "function-definition": FunctionDefinition,
        compartment: Compartment,
        species: Species,
        parameter: Parameter,
        reaction: Reaction,
        "assignment-rule": AssignmentRule,
        "rate-rule": RateRule,
        "algebraic-rule": AlgebraicRule,
        constraint: Constraint,
        event: Event,
        objective: Objective,
        "gene-product": GeneProduct,
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/ComponentSpecificDetails.scss";
</style>
