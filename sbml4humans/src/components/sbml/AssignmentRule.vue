<template>
    <!-- Variable -->
    <div class="data" v-if="info.sid">
        <div class="label"><strong>variable:</strong> {{ info.sid }}</div>
    </div>

    <!-- Math -->
    <div class="data" v-if="info.math">
        <div class="label">
            <strong>math: </strong>
            <katex :mathStr="info.id + '=' + info.math"></katex>
        </div>
    </div>

    <!-- Derived Units -->
    <div class="data" v-if="info.derivedUnits">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex v-bind:mathStr="info.derivedUnits"></katex>
        </div>
    </div>
</template>

<script>
import TYPES from "@/data/sbmlComponents";

import Katex from "@/components/layout/Katex.vue";

export default {
    props: {
        info: TYPES.AssignmentRule,
    },

    components: {
        katex: Katex,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
