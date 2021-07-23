<template>
    <!-- Substance Units -->
    <div class="data" v-if="info.substanceUnits != null">
        <div class="label">
            <strong>Substance Units:</strong> {{ info.substanceUnits }}
        </div>
    </div>

    <!-- Time Units -->
    <div class="data" v-if="info.timeUnits != null">
        <div class="label"><strong>timeUnits:</strong> {{ info.timeUnits }}</div>
    </div>

    <!-- Length Units -->
    <div class="data" v-if="info.lengthUnits != null">
        <div class="label"><strong>lengthUnits:</strong> {{ info.lengthUnits }}</div>
    </div>

    <!-- Area Units -->
    <div class="data" v-if="info.areaUnits != null">
        <div class="label"><strong>areaUnits:</strong> {{ info.areaUnits }}</div>
    </div>

    <!-- Volume Units -->
    <div class="data" v-if="info.volumeUnits != null">
        <div class="label"><strong>volumeUnits:</strong> {{ info.volumeUnits }}</div>
    </div>

    <!-- Extent Units -->
    <div class="data" v-if="info.extentUnits != null">
        <div class="label"><strong>extentUnits:</strong> {{ info.extentUnits }}</div>
    </div>

    <!-- Conversion Factor -->
    <div class="data" v-if="info.conversionFactor != null">
        <div class="label">
            <strong>conversionFactor:</strong> {{ info.conversionFactor }}
        </div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Model objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.Model,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
