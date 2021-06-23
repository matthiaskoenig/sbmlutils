<template>
    <!-- Value -->
    <div class="data" v-if="info.value">
        <div class="label"><strong>value:</strong> {{ info.value }}</div>
    </div>

    <!-- Constant -->
    <div class="data" v-if="info.constant">
        <div class="label"><strong>constant:</strong> {{ info.constant }}</div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units">
        <div class="label">
            <strong>units:</strong>
            <katex v-bind:mathStr="info.units"></katex>
        </div>
    </div>

    <!-- Derived Units -->
    <div class="data" v-if="info.derivedUnits">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex v-bind:mathStr="info.derivedUnits"></katex>
        </div>
    </div>

    <!-- Assignment -->
    <div class="data" v-if="info.assignment">
        <div class="label">
            <strong>assignment:</strong>
            <span>{{ info.assignment.pk }} ({{ info.assignment.sbmlType }})</span>
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
            default: TYPES.Parameter,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
