<template>
    <!-- Value -->
    <div class="data" v-if="info.value">
        <div class="label"><strong>value:</strong> {{ info.value }}</div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units">
        <div class="label"><strong>units:</strong> {{ info.units }}</div>
    </div>

    <!-- Constant -->
    <div class="data" v-if="info.constant">
        <div class="label"><strong>constant:</strong> {{ info.constant }}</div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Parameter objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.Parameter,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
