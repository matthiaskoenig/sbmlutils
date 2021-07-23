<template>
    <div
        v-for="(pks, sbmlType) in getListOfTables"
        :key="sbmlType"
        class="tablesContainer"
    >
        <div ref="Model" v-if="sbmlType === 'Model' && visibility['Model']">
            <model-table :listOfPKs="pks" />
        </div>

        <div
            ref="FunctionDefinition"
            v-if="sbmlType === 'FunctionDefinition' && visibility['FunctionDefinition']"
        >
            <function-definition-table :listOfPKs="pks" />
        </div>

        <div
            ref="Compartment"
            v-if="sbmlType === 'Compartment' && visibility['Compartment']"
        >
            <compartment-table :listOfPKs="pks" />
        </div>

        <div ref="Species" v-if="sbmlType === 'Species' && visibility['Species']">
            <species-table :listOfPKs="pks" />
        </div>

        <div ref="Parameter" v-if="sbmlType === 'Parameter' && visibility['Parameter']">
            <parameter-table :listOfPKs="pks" />
        </div>

        <div
            ref="InitialAssignment"
            v-if="sbmlType === 'InitialAssignment' && visibility['InitialAssignment']"
        >
            <initial-assignment-table :listOfPKs="pks" />
        </div>

        <div
            ref="AssignmentRule"
            v-if="sbmlType === 'AssignmentRule' && visibility['AssignmentRule']"
        >
            <assignment-rule-table :listOfPKs="pks" />
        </div>

        <div ref="RateRule" v-if="sbmlType === 'RateRule' && visibility['RateRule']">
            <rate-rule-table :listOfPKs="pks" />
        </div>

        <div
            ref="AlgebraicRule"
            v-if="sbmlType === 'AlgebraicRule' && visibility['AlgebraicRule']"
        >
            <algebraic-rule-table :listOfPKs="pks" />
        </div>

        <div ref="Reaction" v-if="sbmlType === 'Reaction' && visibility['Reaction']">
            <reaction-table :listOfPKs="pks" />
        </div>

        <div ref="Event" v-if="sbmlType === 'Event' && visibility['Event']">
            <event-table :listOfPKs="pks" />
        </div>

        <div
            ref="UnitDefinition"
            v-if="sbmlType === 'UnitDefinition' && visibility['UnitDefinition']"
        >
            <unit-definition-table :listOfPKs="pks" />
        </div>

        <div ref="Port" v-if="sbmlType === 'Port' && visibility['Port']">
            <port-table :listOfPKs="pks" />
        </div>

        <div ref="Objective" v-if="sbmlType === 'Objective' && visibility['Objective']">
            <objective-table :listOfPKs="pks" />
        </div>

        <div
            ref="Constraint"
            v-if="sbmlType === 'Constraint' && visibility['Constraint']"
        >
            <constraint-table :listOfPKs="pks" />
        </div>

        <div
            ref="GeneProduct"
            v-if="sbmlType === 'GeneProduct' && visibility['GeneProduct']"
        >
            <gene-product-table :listOfPKs="pks" />
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

import "datatables.net-buttons-bs4";
import $ from "jquery";

import ModelTable from "@/components/tables/ModelTable.vue";
import CompartmentTable from "@/components/tables/CompartmentTable.vue";
import SpeciesTable from "@/components/tables/SpeciesTable.vue";
import ParameterTable from "@/components/tables/ParameterTable.vue";
import InitialAssignmentTable from "@/components/tables/InitialAssignmentTable.vue";
import AssignmentRuleTable from "@/components/tables/AssignmentRuleTable.vue";
import RateRuleTable from "@/components/tables/RateRuleTable.vue";
import AlgebraicRuleTable from "@/components/tables/AlgebraicRuleTable.vue";
import ReactionTable from "@/components/tables/ReactionTable.vue";
import EventTable from "@/components/tables/EventTable.vue";
import UnitDefinitionTable from "@/components/tables/UnitDefinitionTable.vue";
import PortTable from "@/components/tables/PortTable.vue";
import ObjectiveTable from "@/components/tables/ObjectiveTable.vue";
import ConstraintTable from "@/components/tables/ConstraintTable.vue";
import GeneProductTable from "@/components/tables/GeneProductTable.vue";
import FunctionDefinitionTable from "@/components/tables/FunctionDefinitionTable.vue";

export default defineComponent({
    components: {
        ModelTable,
        CompartmentTable,
        SpeciesTable,
        ParameterTable,
        InitialAssignmentTable,
        AssignmentRuleTable,
        RateRuleTable,
        AlgebraicRuleTable,
        ReactionTable,
        EventTable,
        UnitDefinitionTable,
        PortTable,
        ObjectiveTable,
        ConstraintTable,
        GeneProductTable,
        FunctionDefinitionTable,
    },

    mounted(): void {
        $(document).ready(() => {
            $("table").DataTable();
        });
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
.tablesContainer {
    width: 100%;
    padding: 0 1%;
}

label {
    font-size: small;
    display: flex;
}

.dataTables_filter label {
    display: flex;
    margin: 15px 5px !important;
}

.dataTables_filter .form-control {
    display: flex;
    margin: -5px 5px !important;
}

.dataTables_length .form-control {
    width: 75px !important;
    margin: 10px 5px !important;
}

.dataTables_paginate li {
    padding: 0px 0px !important;
    margin: 2px 5px !important;
    border-color: white !important;
    border-radius: 0 !important;
}

.dataTables_info {
    font-size: small;
}

.page-link {
    font-size: small;
    border-radius: 0 !important;
    z-index: 0 !important;
}
</style>
