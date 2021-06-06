<template>
    <div class="container">
        <a-descriptions bordered :size="size">
            <a-descriptions-item label="Spatial Dimensions">{{
                info.spatialDimensions
            }}</a-descriptions-item>
            <a-descriptions-item label="Size">{{ info.size }}</a-descriptions-item>
            <a-descriptions-item label="Units">{{ info.units }}</a-descriptions-item>
            <a-descriptions-item label="Constant">{{
                info.constant
            }}</a-descriptions-item>
        </a-descriptions>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.Reaction,
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
