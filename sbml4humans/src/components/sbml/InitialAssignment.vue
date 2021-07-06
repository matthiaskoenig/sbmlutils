<template>
    <!-- Symbol -->
    <div class="data" v-if="info.symbol">
        <div class="label"><strong>symbol:</strong> {{ info.symbol }}</div>
    </div>

    <!-- Math -->
    <div class="data" v-if="info.math">
        <div class="label"><strong>math:</strong> {{ info.math }}</div>
    </div>

    <!-- Derived Units -->
    <div class="data" v-if="info.derivedUnits">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex v-bind:mathStr="info.derivedUnits"></katex>
        </div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Parameter objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.InitialAssignment,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/SBase.scss";
</style>
