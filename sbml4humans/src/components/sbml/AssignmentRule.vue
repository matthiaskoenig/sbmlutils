<template>
    <!-- Variable -->
    <div class="data" v-if="info.sid">
        <div class="label"><strong>variable:</strong> {{ info.sid }}</div>
    </div>

    <!-- Math -->
    <div class="data" v-if="info.math">
        <div class="label">
            <strong>math: </strong><!-- ({{info.math}})-->
            <katex :mathStr="info.id + '=' + info.math"></katex>
        </div>
    </div>

    <!-- Units (not working for now) -->
    <div class="data" v-if="info.units">
        <div class="label">
            <strong>units:</strong>
            <div class="ml-4">
                <div v-if="info.units">{{ info.units }}</div>
            </div>
        </div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

import Katex from "@/components/layout/Katex.vue";

export default {
    props: {
        info: TYPES.Rule,
    },

    components: {
        katex: Katex,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
