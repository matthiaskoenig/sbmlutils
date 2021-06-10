<template>
    <!-- Math -->
    <div class="data" v-if="info.math">
        <div class="label"><strong>Math:</strong> <span v-html="info.math"></span></div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.FunctionDefinition,
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
