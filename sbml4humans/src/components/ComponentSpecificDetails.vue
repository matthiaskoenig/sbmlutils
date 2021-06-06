<template>
    <div id="compartmentDiv" v-if="sbmlType === 'Compartment'">
        <compartment></compartment>
    </div>
</template>

<script>
import Compartment from "@/components/sbml/Compartment.vue";

export default {
    props: {
        sbmlType: String,
        info: {},
    },

    components: {
        compartment: Compartment,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/ComponentSpecificDetails.vue";
</style>
