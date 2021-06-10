<template>
    <!-- Math -->
    <div class="data" v-if="info.math">
        <div class="label"><strong>Math:</strong> <span v-html="info.math"></span></div>
    </div>

    <!-- Message -->
    <div class="data" v-if="info.message">
        <div class="label"><strong>Message:</strong>{{ info.message }}</div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.Constraint,
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
