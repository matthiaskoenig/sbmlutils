<template>
    <div
        class="tables-container"
        v-for="(pks, sbmlType) in getListOfTables"
        v-bind:key="sbmlType"
    >
        <div ref="Model" v-if="sbmlType === 'Model' && visibility['Model']">
            <table-of-models v-bind:listOfPKs="pks"></table-of-models>
        </div>

        <div
            ref="FunctionDefinition"
            v-if="sbmlType === 'FunctionDefinition' && visibility['FunctionDefinition']"
        >
            <table-of-function-definitions
                v-bind:listOfPKs="pks"
            ></table-of-function-definitions>
        </div>

        <div
            ref="Compartment"
            v-if="sbmlType === 'Compartment' && visibility['Compartment']"
        >
            <table-of-compartments v-bind:listOfPKs="pks"></table-of-compartments>
        </div>

        <div ref="Species" v-if="sbmlType === 'Species' && visibility['Species']">
            <table-of-species v-bind:listOfPKs="pks"></table-of-species>
        </div>

        <div ref="Parameter" v-if="sbmlType === 'Parameter' && visibility['Parameter']">
            <table-of-parameters v-bind:listOfPKs="pks"></table-of-parameters>
        </div>

        <div
            ref="InitialAssignment"
            v-if="sbmlType === 'InitialAssignment' && visibility['InitialAssignment']"
        >
            <table-of-initial-assignments
                v-bind:listOfPKs="pks"
            ></table-of-initial-assignments>
        </div>

        <div
            ref="AssignmentRule"
            v-if="sbmlType === 'AssignmentRule' && visibility['AssignmentRule']"
        >
            <table-of-assignment-rules
                v-bind:listOfPKs="pks"
            ></table-of-assignment-rules>
        </div>

        <div ref="RateRule" v-if="sbmlType === 'RateRule' && visibility['RateRule']">
            <table-of-rate-rules v-bind:listOfPKs="pks"></table-of-rate-rules>
        </div>

        <div
            ref="AlgebraicRule"
            v-if="sbmlType === 'AlgebraicRule' && visibility['AlgebraicRule']"
        >
            <table-of-algebraic-rules v-bind:listOfPKs="pks"></table-of-algebraic-rules>
        </div>

        <div ref="Reaction" v-if="sbmlType === 'Reaction' && visibility['Reaction']">
            <table-of-reactions v-bind:listOfPKs="pks"></table-of-reactions>
        </div>

        <div ref="Event" v-if="sbmlType === 'Event' && visibility['Event']">
            <table-of-events v-bind:listOfPKs="pks"></table-of-events>
        </div>

        <div
            ref="UnitDefinition"
            v-if="sbmlType === 'UnitDefinition' && visibility['UnitDefinition']"
        >
            <table-of-unit-definitions
                v-bind:listOfPKs="pks"
            ></table-of-unit-definitions>
        </div>

        <div ref="Port" v-if="sbmlType === 'Port' && visibility['Port']">
            <table-of-ports v-bind:listOfPKs="pks"></table-of-ports>
        </div>

        <div ref="Objective" v-if="sbmlType === 'Objective' && visibility['Objective']">
            <table-of-objectives v-bind:listOfPKs="pks"></table-of-objectives>
        </div>

        <div
            ref="Constraint"
            v-if="sbmlType === 'Constraint' && visibility['Constraint']"
        >
            <table-of-constraints v-bind:listOfPKs="pks"></table-of-constraints>
        </div>

        <div
            ref="GeneProduct"
            v-if="sbmlType === 'GeneProduct' && visibility['GeneProduct']"
        >
            <table-of-gene-products v-bind:listOfPKs="pks"></table-of-gene-products>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

import TableOfModels from "@/components/tables/Model.vue";
import TableOfCompartments from "@/components/tables/Compartment.vue";
import TableOfSpecies from "@/components/tables/Species.vue";
import TableOfParameters from "@/components/tables/Parameter.vue";
import TableOfInitialAssignments from "@/components/tables/InitialAssignment.vue";
import TableOfAssignmentRules from "@/components/tables/AssignmentRule.vue";
import TableOfRateRules from "@/components/tables/RateRule.vue";
import TableOfAlgebraicRules from "@/components/tables/AlgebraicRule.vue";
import TableOfReactions from "@/components/tables/Reaction.vue";
import TableOfEvents from "@/components/tables/Event.vue";
import TableOfUnitDefinitions from "@/components/tables/UnitDefinition.vue";
import TableOfPorts from "@/components/tables/Port.vue";
import TableOfObjectives from "@/components/tables/Objective.vue";
import TableOfConstraints from "@/components/tables/Constraint.vue";
import TableOfGeneProducts from "@/components/tables/GeneProduct.vue";
import TableOfFunctionDefinitions from "@/components/tables/FunctionDefinition.vue";

export default defineComponent({
    components: {
        "table-of-models": TableOfModels,
        "table-of-compartments": TableOfCompartments,
        "table-of-species": TableOfSpecies,
        "table-of-parameters": TableOfParameters,
        "table-of-initial-assignments": TableOfInitialAssignments,
        "table-of-assignment-rules": TableOfAssignmentRules,
        "table-of-rate-rules": TableOfRateRules,
        "table-of-algebraic-rules": TableOfAlgebraicRules,
        "table-of-reactions": TableOfReactions,
        "table-of-events": TableOfEvents,
        "table-of-unit-definitions": TableOfUnitDefinitions,
        "table-of-ports": TableOfPorts,
        "table-of-objectives": TableOfObjectives,
        "table-of-constraints": TableOfConstraints,
        "table-of-gene-products": TableOfGeneProducts,
        "table-of-function-definitions": TableOfFunctionDefinitions,
    },

    methods: {
        scrollToElement(sbmlType: string) {
            const el: HTMLElement = this.$refs[sbmlType] as HTMLElement;
            if (el) {
                // Use el.scrollIntoView() to instantly scroll to the element
                el.scrollIntoView({ behavior: "smooth" });
            }
        },
    },

    computed: {
        getListOfTables(): Record<string, Array<string>> {
            let tables: Record<string, Array<string>> = {};

            const componentPKsMap: Record<string, Array<string>> =
                store.getters.componentPKsMap;

            for (let sbmlType in componentPKsMap) {
                if (componentPKsMap[sbmlType].length > 0) {
                    tables[sbmlType] = componentPKsMap[sbmlType];
                }
            }

            return tables;
        },

        visibility(): Record<string, boolean> {
            return store.state.visibility;
        },

        currentFocussedTable() {
            return store.state.currentFocussedTable;
        },
    },

    watch: {
        currentFocussedTable: {
            handler(current) {
                this.scrollToElement(current);
            },
            deep: true,
            immediate: true,
        },
    },
});
</script>

<style lang="scss">
.tables-container {
    width: 100%;
    overflow-x: scroll;
}
</style>
