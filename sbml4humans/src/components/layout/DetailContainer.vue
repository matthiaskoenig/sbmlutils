<template>
    <div class="detail-container">
        <!---- ============================== SBase Info Starts ============================= --->
        <sbase v-bind:info="info"></sbase>
        <!---- ============================== SBase Info Ends =============================   --->

        <!---- ==================== Component Specific Info Starts ========================   --->
        <component-specific-details
            v-bind:info="info"
            v-bind:sbmlType="sbmlType"
        ></component-specific-details>
        <!---- ==================== Component Specific Info Ends  =========================   --->
    </div>
</template>

<script lang="ts">
import store from "@/store/index";

/* Components */
import SBase from "@/components/sbml/SBase.vue";
import ComponentSpecificDetails from "@/components/layout/ComponentSpecificDetails.vue";

/*
 * Component to display detailed information about the selected SBML Component.
 */
export default {
    components: {
        sbase: SBase,
        "component-specific-details": ComponentSpecificDetails,
    },

    computed: {
        /**
         * Reactively returns the detailInfo from Vuex state/localStorage.
         */
        info(): Record<string, unknown> {
            return store.state.detailInfo;
        },

        /**
         * Reactively returns the sbmlType of the currently selected SBML Component's
         * details.
         */
        sbmlType(): StringConstructor {
            return store.state.detailInfo.sbmlType;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/DetailContainer.scss";
</style>
