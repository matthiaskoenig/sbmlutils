<template>
    <!-- Unit String -->
    <div class="data" v-if="info.units">
        <div class="label">
            <strong>units:</strong>
            <katex v-bind:mathStr="info.units"></katex>
        </div>
    </div>
</template>

<script>
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of UnitDefinition objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.UnitDefinition,
        },
    },

    components: {
        katex: Katex,
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
