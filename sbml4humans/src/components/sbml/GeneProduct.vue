<template>
    <!-- Label -->
    <div class="data" v-if="info.label">
        <div class="label"><strong>label:</strong> {{ info.label }}</div>
    </div>

    <!-- Associated Species -->
    <div class="data" v-if="info.associatedSpecies">
        <div class="label">
            <strong>associatedSpecies:</strong> {{ info.associatedSpecies }}
        </div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.GeneProduct,
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
