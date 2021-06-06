<template>
    <!-- Spatial Dimensions -->
    <div class="data" v-if="info.spatialDimensions">
        <div class="label">
            <strong>Spatial Dimensions:</strong> {{ info.spatialDimensions }}
        </div>
    </div>

    <!-- Size -->
    <div class="data" v-if="info.size">
        <div class="label"><strong>Size:</strong> {{ info.size }}</div>
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
        info: TYPES.Compartment,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
