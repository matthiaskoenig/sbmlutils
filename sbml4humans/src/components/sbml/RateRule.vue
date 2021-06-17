<template>
    <!-- Variable -->
    <div class="data" v-if="info.sid">
        <div class="label"><strong>variable:</strong> {{ info.sid }}</div>
    </div>

    <!-- Math -->
    <div class="data" v-if="info.math">
        <div class="label">
            <strong>math:</strong>
            <katex :mathStr="info.math"></katex>
        </div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units">
        <div class="label">
            <strong>units:</strong>
            <div class="ml-4">
                <div v-if="info.units.math">math: {{ info.units.math }}</div>
                <div v-if="info.units.unitTerms">
                    unitTerms: {{ info.units.unitTerms }}
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.Rule,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
