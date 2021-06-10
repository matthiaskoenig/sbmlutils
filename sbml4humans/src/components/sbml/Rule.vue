<template>
    <!-- Variable -->
    <div class="data" v-if="info.sid">
        <div class="label"><strong>Variable:</strong> {{ info.sid }}</div>
    </div>

    <!-- Assignment -->
    <div class="data" v-if="info.assignment">
        <div class="label"><strong>Assignment:</strong> {{ info.assignment }}</div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units">
        <div class="label">
            <strong>Units:</strong>
            <div class="ml-4">
                <div v-if="info.units.math">Math: {{ info.units.math }}</div>
                <div v-if="info.units.unitTerms">
                    Unit Terms: {{ info.units.unitTerms }}
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

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
