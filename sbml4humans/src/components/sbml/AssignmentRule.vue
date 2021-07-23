<template>
    <!-- Variable -->
    <div class="data" v-if="info.sid != null">
        <div class="label"><strong>variable:</strong> {{ info.sid }}</div>
    </div>

    <!-- Math -->
    <div class="data" v-if="info.math != null">
        <div class="label">
            <strong>math: </strong>
            <katex :mathStr="info.id + '=' + info.math"></katex>
        </div>
    </div>

    <!-- Derived Units -->
    <div class="data" v-if="info.derivedUnits != null">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex :mathStr="info.derivedUnits"></katex>
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
