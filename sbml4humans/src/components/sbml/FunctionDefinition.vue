<template>
    <!-- Math -->
    <div class="data" v-if="info.math != null">
        <div class="label">
            <strong>math:</strong>
            <katex :mathStr="info.math"></katex>
        </div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of FunctionDefinition objects.
 */
export default defineComponent({
    components: {
        katex: Katex,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.FunctionDefinition,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
