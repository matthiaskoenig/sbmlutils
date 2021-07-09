<template>
    <!-- Compartment -->
    <div class="data" v-if="info.compartment">
        <div class="label"><strong>compartment: </strong></div>
        <div class="ml-3">
            <SBMLLink
                v-bind:pk="'Compartment:' + info.compartment"
                v-bind:sbmlType="String('Compartment')"
            ></SBMLLink>
        </div>
    </div>

    <!-- Initial Amount -->
    <div class="data" v-if="info.initialAmount">
        <div class="label">
            <strong>initialAmount:</strong> {{ info.initialAmount }}
        </div>
    </div>

    <!-- Initial Concentration -->
    <div class="data" v-if="info.initialConcentration">
        <div class="label">
            <strong>initialConcentration:</strong> {{ info.initialConcentration }}
        </div>
    </div>

    <!-- Substance Units -->
    <div class="data" v-if="info.substanceUnits">
        <div class="label">
            <strong>substanceUnits:</strong> {{ info.substanceUnits }}
        </div>
    </div>

    <!-- Has Only Substance Units -->
    <div class="data" v-if="info.hasOnlySubstanceUnits">
        <div class="label">
            <strong>hasOnlySubstanceUnits:</strong> {{ info.hasOnlySubstanceUnits }}
        </div>
    </div>

    <!-- Boundary Condition -->
    <div class="data" v-if="info.boundaryCondition">
        <div class="label">
            <strong>boundaryCondition:</strong> {{ info.boundaryCondition }}
        </div>
    </div>

    <!-- Constant -->
    <div class="data" v-if="info.constant">
        <div class="label"><strong>constant:</strong> {{ info.constant }}</div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units">
        <div class="label">
            <strong>units:</strong>
            <Katex v-bind:mathStr="info.units" />
        </div>
    </div>

    <!-- Derived Units -->
    <div class="data" v-if="info.derivedUnits">
        <div class="label">
            <strong>derivedUnits:</strong>
            <Katex v-bind:mathStr="info.derivedUnits" />
        </div>
    </div>

    <!-- Assignment -->
    <div class="data" v-if="info.assignment">
        <div class="label">
            <strong>assignment:</strong>
            <span>{{ info.assignment.pk }} ({{ info.assignment.sbmlType }})</span>
        </div>
    </div>

    <!-- Conversion Factor -->
    <div
        class="data"
        v-if="
            info.conversionFactor &&
            (info.conversionFactor.sid ||
                info.conversionFactor.value ||
                info.conversionFactor.units)
        "
    >
        <div class="label">
            <strong>Conversion Factor:</strong>
            <div class="mb-4">
                <ul title="Conversion Factor">
                    <li v-if="info.conversionFactor.sid">
                        sid: {{ info.conversionFactor.sid }}
                    </li>
                    <li v-if="info.conversionFactor.value">
                        value: {{ info.conversionFactor.value }}
                    </li>
                    <li v-if="info.conversionFactor.units">
                        units: {{ info.conversionFactor.units }}
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <!-- FBC Data -->
    <div class="data" v-if="info.fbc && (info.fbc.formula || info.fbc.charge)">
        <div class="label">
            <strong>FBC Data:</strong>
            <div class="mb-4">
                <ul title="FBC Data">
                    <li v-if="info.fbc.formula">formula: {{ info.fbc.formula }}</li>
                    <li v-if="info.fbc.charge">charge: {{ info.fbc.charge }}</li>
                </ul>
            </div>
        </div>
    </div>

    <div class="row col-12">
        <!-- List of Reactant Reactions -->
        <div class="col-sm-3 data" v-if="info.reactant && info.reactant.length">
            <div class="label">
                <strong>reactant:</strong>
            </div>
            <div class="ml-4">
                <SBMLLink
                    v-for="reactant in info.reactant"
                    v-bind:key="reactant"
                    v-bind:pk="reactant"
                    v-bind:sbmlType="String('Reaction')"
                ></SBMLLink>
            </div>
        </div>
        <!-- List of Product Reactions -->
        <div class="col-sm-3 data" v-if="info.product && info.product.length">
            <div class="label">
                <strong>product:</strong>
            </div>
            <div class="ml-4">
                <SBMLLink
                    v-for="product in info.product"
                    v-bind:key="product"
                    v-bind:pk="product"
                    v-bind:sbmlType="String('Reaction')"
                ></SBMLLink>
            </div>
        </div>

        <!-- List of Modifier Reactions -->
        <div class="col-sm-3 data" v-if="info.modifier && info.modifier.length">
            <div class="label">
                <strong>modifier:</strong>
            </div>
            <div class="ml-4">
                <SBMLLink
                    v-for="modifier in info.modifier"
                    v-bind:key="modifier"
                    v-bind:pk="modifier"
                    v-bind:sbmlType="String('Reaction')"
                ></SBMLLink>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import SBMLLink from "@/components/layout/SBMLLink.vue";
import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of Species objects.
 */
export default defineComponent({
    components: {
        Katex,
        SBMLLink,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Species,
        },
    },

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
