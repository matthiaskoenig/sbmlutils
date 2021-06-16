<template>
    <!-- Compartment -->
    <div class="data" v-if="info.compartment">
        <div class="label"><strong>compartment:</strong> {{ info.compartment }}</div>
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
</template>

<script>
import TYPES from "@/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Species objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.Species,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Species.scss";
</style>
