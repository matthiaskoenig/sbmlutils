<template>
    <div
        v-for="(pks, sbmlType) in getListOfTables"
        :key="sbmlType"
        class="tablesContainer"
    >
        <div ref="Model" v-if="sbmlType === 'Model' && visibility['Model']">
            <model-table ref="#model-table" :listOfPKs="pks" />
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

        <div ref="Submodel" v-if="sbmlType === 'Submodel' && visibility['Submodel']">
            <submodel-table :listOfPKs="pks" />
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

<script>
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";
import "datatables.net";
import "datatables.net-buttons-bs4";
import "datatables.net-dt";
import $ from "jquery";

import ModelTable from "@/components/tables/ModelTable.vue";
import CompartmentTable from "@/components/tables/CompartmentTable.vue";
import SpeciesTable from "@/components/tables/SpeciesTable.vue";
import SubmodelTable from "@/components/tables/SubmodelTable.vue";
import ParameterTable from "@/components/tables/ParameterTable.vue";
import InitialAssignmentTable from "@/components/tables/InitialAssignmentTable.vue";
import AssignmentRuleTable from "@/components/tables/AssignmentRuleTable.vue";
import RateRuleTable from "@/components/tables/RateRuleTable.vue";
import AlgebraicRuleTable from "@/components/tables/AlgebraicRuleTable.vue";
import ReactionTable from "@/components/tables/ReactionTable.vue";
//import ReactionPrimeTable from "@/components/tables/ReactionPrimeTable.vue";
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
        SubmodelTable,
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

    created() {
        $(document).ready(() => {
            $("table").DataTable();
        });
    },

    methods: {
        scrollToElement(sbmlType) {
            const el = this.$refs[sbmlType];
            if (el) {
                // Use el.scrollIntoView() to instantly scroll to the element
                el.scrollIntoView({ behavior: "smooth" });
            }
        },

        /**
         * Filters SBML objects on the basis of the search query.
         * @param sbases Array of SBML objects to filter.
         * @param searchQuery The search query to look for in the SBML objects' data
         */
        filterForSearchResults(sBasePKs, searchQuery = "") {
            if (searchQuery === "") return sBasePKs;

            const allSBMLComponents = store.state.allObjectsMap;

            let searchedSBasePKs = [];
            searchedSBasePKs.push(
                ...sBasePKs.filter((pk) => {
                    const sbmlComponent = allSBMLComponents[pk];
                    const componentMeta =
                        sbmlComponent.id + sbmlComponent.metaId + sbmlComponent.sbo;
                    return componentMeta
                        .replace(" ", "")
                        .toLowerCase()
                        .includes(searchQuery.replace(" ", "").toLowerCase());
                })
            );
            return searchedSBasePKs;
        },
    },

    computed: {
        getListOfTables() {
            let tables = {};

            const componentPKsMap = store.getters.componentPKsMap;

            for (let sbmlType in componentPKsMap) {
                if (componentPKsMap[sbmlType].length > 0) {
                    tables[sbmlType] = this.filterForSearchResults(
                        componentPKsMap[sbmlType],
                        this.searchQuery
                    );
                }
            }

            return tables;
        },

        visibility() {
            return store.state.visibility;
        },

        currentFocussedTable() {
            return store.state.currentFocussedTable;
        },

        searchQuery() {
            return store.state.searchQuery;
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

.dataTables_wrapper .row {
    width: 100% !important;
    padding: 0 0 !important;
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

.pagination {
    width: fit-content;
    margin-left: auto;
}

table.dataTable > thead > tr > th:not(.sorting_disabled),
table.dataTable > thead > tr > td:not(.sorting_disabled) {
    padding-right: 30px;
}

table.dataTable > thead .sorting,
table.dataTable > thead .sorting_asc,
table.dataTable > thead .sorting_desc,
table.dataTable > thead .sorting_asc_disabled,
table.dataTable > thead .sorting_desc_disabled {
    cursor: pointer;
    position: relative;
}

table.dataTable > thead .sorting:before,
table.dataTable > thead .sorting:after,
table.dataTable > thead .sorting_asc:before,
table.dataTable > thead .sorting_asc:after,
table.dataTable > thead .sorting_desc:before,
table.dataTable > thead .sorting_desc:after,
table.dataTable > thead .sorting_asc_disabled:before,
table.dataTable > thead .sorting_asc_disabled:after,
table.dataTable > thead .sorting_desc_disabled:before,
table.dataTable > thead .sorting_desc_disabled:after {
    position: absolute;
    display: inline;
    opacity: 0.1;
    margin: auto 2px;
}

table.dataTable > thead .sorting:before,
table.dataTable > thead .sorting_asc:before,
table.dataTable > thead .sorting_desc:before,
table.dataTable > thead .sorting_asc_disabled:before,
table.dataTable > thead .sorting_desc_disabled:before {
    right: 1em;
    content: "↑";
    margin-top: auto;
    margin: 0 2px;
}

table.dataTable > thead .sorting:after,
table.dataTable > thead .sorting_asc:after,
table.dataTable > thead .sorting_desc:after,
table.dataTable > thead .sorting_asc_disabled:after,
table.dataTable > thead .sorting_desc_disabled:after {
    right: 0.5em;
    content: "↓";
    margin-top: auto;
    margin: 0 2px;
}

table.dataTable > thead .sorting_asc:before,
table.dataTable > thead .sorting_desc:after {
    opacity: 1;
}

table.dataTable > thead .sorting_asc_disabled:before,
table.dataTable > thead .sorting_desc_disabled:after {
    opacity: 0;
}
</style>
