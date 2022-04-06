<template>
    <div id="documentDiv" v-if="sbmlType === 'SBMLDocument'">
        <SBMLDocument :info="info" />
    </div>

    <div id="modelDiv" v-if="sbmlType === 'Model'">
        <model :info="info" />
    </div>

    <div id="portDiv" v-if="sbmlType === 'Port'">
        <port :info="info" />
    </div>

    <div id="functionDefinitionDiv" v-if="sbmlType === 'FunctionDefinition'">
        <function-definition :info="info" />
    </div>

    <div id="unitDefinitionDiv" v-if="sbmlType === 'UnitDefinition'">
        <unit-definition :info="info" />
    </div>

    <div id="compartmentDiv" v-if="sbmlType === 'Compartment'">
        <compartment :info="info" />
    </div>

    <div id="speciesDiv" v-if="sbmlType === 'Species'">
        <species :info="info" />
    </div>

    <div id="parameterDiv" v-if="sbmlType === 'Parameter'">
        <parameter :info="info" />
    </div>

    <div id="reactionDiv" v-if="sbmlType === 'Reaction'">
        <reaction :info="info" />
    </div>

    <div id="assignmentRuleDiv" v-if="sbmlType === 'AssignmentRule'">
        <assignment-rule :info="info" />
    </div>

    <div id="initialAssignmentDiv" v-if="sbmlType === 'InitialAssignment'">
        <initial-assignment :info="info" />
    </div>

    <div id="rateRuleDiv" v-if="sbmlType === 'RateRule'">
        <rate-rule :info="info" />
    </div>

    <div id="algebraicRuleDiv" v-if="sbmlType === 'AlgebraicRule'">
        <algebraic-rule :info="info" />
    </div>

    <div id="constraintDiv" v-if="sbmlType === 'Constraint'">
        <constraint :info="info" />
    </div>

    <div id="eventDiv" v-if="sbmlType === 'Event'">
        <event :info="info" />
    </div>

    <div id="objectiveDiv" v-if="sbmlType === 'Objective'">
        <objective :info="info" />
    </div>

    <div id="geneProductDiv" v-if="sbmlType === 'GeneProduct'">
        <gene-product :info="info" />
    </div>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import SBMLDocument from "@/components/sbml/SBMLDocument.vue";
import Model from "@/components/sbml/Model.vue";
import Port from "@/components/sbml/Port.vue";
import FunctionDefinition from "@/components/sbml/FunctionDefinition.vue";
import UnitDefinition from "@/components/sbml/UnitDefinition.vue";
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
import InitialAssignment from "@/components/sbml/InitialAssignment.vue";

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
        InitialAssignment,
        SBMLDocument,
        Model,
        Port,
        FunctionDefinition,
        UnitDefinition,
        Compartment,
        Species,
        Parameter,
        Reaction,
        AssignmentRule,
        RateRule,
        AlgebraicRule,
        Constraint,
        Event,
        Objective,
        GeneProduct,
    },
});
</script>

<style lang="scss" scoped>
div {
    width: 100%;
}
</style>
