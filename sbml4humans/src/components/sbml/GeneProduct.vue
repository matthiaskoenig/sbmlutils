<template>
    <!-- Label -->
    <div class="data" v-if="info.label">
        <div class="label"><strong>label:</strong> {{ info.label }}</div>
    </div>

    <!-- Associated Species -->
    <div class="data" v-if="info.associatedSpecies">
        <div class="label">
            <strong>associatedSpecies:</strong> {{ info.associatedSpecies }}
        </div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of GeneProduct objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.GeneProduct,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
