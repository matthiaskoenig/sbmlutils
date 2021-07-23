<template>
    <!-- Math -->
    <div class="data" v-if="info.math">
        <div class="label">
            <strong>math:</strong>
            <katex :mathStr="info.math"></katex>
        </div>
    </div>

    <!-- Message -->
    <div class="data" v-if="info.message">
        <div class="label"><strong>message:</strong>{{ info.message }}</div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of Constraint objects.
 */
export default defineComponent({
    components: {
        katex: Katex,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Constraint,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
