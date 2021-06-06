<template>
    <!-- Compartment -->
    <div class="data" v-if="info.compartment">
        <div class="label"><strong>Compartment:</strong> {{ info.compartment }}</div>
    </div>

    <!-- Initial Amount -->
    <div class="data" v-if="info.initialAmount">
        <div class="label">
            <strong>Initial Amount:</strong> {{ info.initialAmount }}
        </div>
    </div>

    <!-- Initial Concentration -->
    <div class="data" v-if="info.initialConcentration">
        <div class="label">
            <strong>Initial Concentration:</strong> {{ info.initialConcentration }}
        </div>
    </div>

    <!-- Substance Units -->
    <div class="data" v-if="info.substanceUnits">
        <div class="label">
            <strong>Substance Units:</strong> {{ info.substanceUnits }}
        </div>
    </div>

    <!-- Has Only Substance Units -->
    <div class="data" v-if="info.hasOnlySubstanceUnits">
        <div class="label">
            <strong>Has Only Substance Units:</strong> {{ info.hasOnlySubstanceUnits }}
        </div>
    </div>

    <!-- Boundary Condition -->
    <div class="data" v-if="info.boundaryCondition">
        <div class="label">
            <strong>Boundary Condition:</strong> {{ info.boundaryCondition }}
        </div>
    </div>

    <!-- Constant -->
    <div class="data" v-if="info.constant">
        <div class="label"><strong>Constant:</strong> {{ info.constant }}</div>
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
                        SID: {{ info.conversionFactor.sid }}
                    </li>
                    <li v-if="info.conversionFactor.value">
                        Value: {{ info.conversionFactor.value }}
                    </li>
                    <li v-if="info.conversionFactor.units">
                        Units: {{ info.conversionFactor.units }}
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
                    <li v-if="info.fbc.formula">Formula: {{ info.fbc.formula }}</li>
                    <li v-if="info.fbc.charge">Charge: {{ info.fbc.charge }}</li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.Species,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Species.scss";
</style>
