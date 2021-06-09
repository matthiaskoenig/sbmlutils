<template>
    <!-- Value -->
    <div class="data" v-if="info.value">
        <div class="label"><strong>Value:</strong> {{ info.value }}</div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units">
        <div class="label"><strong>Units:</strong> {{ info.units }}</div>
    </div>

    <!-- Constant -->
    <div class="data" v-if="info.constant">
        <div class="label"><strong>Constant:</strong> {{ info.constant }}</div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.Parameter,
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
