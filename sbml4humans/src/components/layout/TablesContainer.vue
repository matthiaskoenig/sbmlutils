<template>
    <div v-for="(pks, sbmlType) in getListOfTables" :key="sbmlType">
        <div ref="Model" v-if="sbmlType === 'Model' && visibility['Model']">
            <model-table ref="#model-table" :listOfPKs="pks" />
        </div>

        <div
            ref="ExternalModelDefinition"
            v-if="
                sbmlType === 'ExternalModelDefinition' &&
                visibility['ExternalModelDefinition']
            "
        >
            <external-model-definition-table
                ref="#externalModeDefinition-table"
                :listOfPKs="pks"
            />
        </div>

        <div
            ref="ModelDefinition"
            v-if="sbmlType === 'ModelDefinition' && visibility['ModelDefinition']"
        >
            <model-definition-table ref="#modeDefinition-table" :listOfPKs="pks" />
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

import ModelTable from "@/components/tables/ModelTable.vue";
import ExternalModelDefinitionTable from "@/components/tables/ExternalModelDefinitionTable.vue";
import ModelDefinitionTable from "@/components/tables/ModelDefinitionTable.vue";
import CompartmentTable from "@/components/tables/CompartmentTable.vue";
import SpeciesTable from "@/components/tables/SpeciesTable.vue";
import SubmodelTable from "@/components/tables/SubmodelTable.vue";
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
        ExternalModelDefinitionTable,
        ModelDefinitionTable,
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

            // THIS IS BAD CURRENTLY
            const allSBMLComponents = store.state.allObjectsMap;

            let searchedSBasePKs = [];
            searchedSBasePKs.push(
                ...sBasePKs.filter((pk) => {
                    const sbmlComponent = allSBMLComponents[pk];
                    return sbmlComponent.searchUtilField
                        .toLowerCase()
                        .includes(searchQuery.toLowerCase());
                })
            );
            return searchedSBasePKs;
        },
    },

    computed: {
        getListOfTables() {
            let tables = {};

            const componentPKsMap = store.getters.componentPKsMap;
            const searchedSBasesCounts = store.state.searchedSBasesCounts;

            // THIS IS A GOOD STRATEGY FOR GLOBAL FILTERING
            for (let sbmlType in componentPKsMap) {
                if (componentPKsMap[sbmlType].length > 0) {
                    tables[sbmlType] = this.filterForSearchResults(
                        componentPKsMap[sbmlType],
                        this.searchQuery
                    );
                    searchedSBasesCounts[sbmlType] = tables[sbmlType].length;
                }
            }
            store.dispatch("updateSearchedSBasesCounts", searchedSBasesCounts);
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

<style lang="scss"></style>
