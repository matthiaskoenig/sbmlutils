<template>
    <!-- Spatial Dimensions -->
    <div class="data" v-if="info.spatialDimensions">
        <div class="label">
            <strong>spatialDimensions:</strong> {{ info.spatialDimensions }}
        </div>
    </div>

    <!-- Size -->
    <div class="data" v-if="info.size">
        <div class="label"><strong>size:</strong> {{ info.size }}</div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units">
        <div class="label">
            <strong>units:</strong>
            <katex v-bind:mathStr="info.units"></katex>
        </div>
    </div>

    <!-- Constant -->
    <div class="data" v-if="info.constant">
        <div class="label"><strong>constant:</strong> {{ info.constant }}</div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of Compartment objects.
 */
export default defineComponent({
    components: {
        katex: Katex,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Compartment,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
