<template>
    <!-- Math -->
    <div class="data" v-if="info.math">
        <div class="label"><strong>math:</strong> <span v-html="info.math"></span></div>
    </div>

    <!-- Message -->
    <div class="data" v-if="info.message">
        <div class="label"><strong>message:</strong>{{ info.message }}</div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Constraint objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.Constraint,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
