<template>
    <!-- Substance Units -->
    <div class="data" v-if="info.substanceUnits">
        <div class="label">
            <strong>Substance Units:</strong> {{ info.substanceUnits }}
        </div>
    </div>

    <!-- Time Units -->
    <div class="data" v-if="info.timeUnits">
        <div class="label"><strong>Time Units:</strong> {{ info.timeUnits }}</div>
    </div>

    <!-- Length Units -->
    <div class="data" v-if="info.lengthUnits">
        <div class="label"><strong>Length Units:</strong> {{ info.lengthUnits }}</div>
    </div>

    <!-- Area Units -->
    <div class="data" v-if="info.areaUnits">
        <div class="label"><strong>Area Units:</strong> {{ info.areaUnits }}</div>
    </div>

    <!-- Volume Units -->
    <div class="data" v-if="info.volumeUnits">
        <div class="label"><strong>Volume Units:</strong> {{ info.volumeUnits }}</div>
    </div>

    <!-- Extent Units -->
    <div class="data" v-if="info.extentUnits">
        <div class="label"><strong>Extent Units:</strong> {{ info.extentUnits }}</div>
    </div>

    <!-- Conversion Factor -->
    <div class="data" v-if="info.conversionFactor">
        <div class="label">
            <strong>Conversion Factor:</strong> {{ info.conversionFactor }}
        </div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.Model,
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
