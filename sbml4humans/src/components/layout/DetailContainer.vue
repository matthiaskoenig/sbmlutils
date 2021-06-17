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

        <!---- ==================== XML Container Starts ====================== -->
        <xml-container v-if="info.xml" v-bind:xml="info.xml"></xml-container>
        <!---- ==================== XML Container Ends ====================== -->
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import SBase from "@/components/sbml/SBase.vue";
import ComponentSpecificDetails from "@/components/layout/ComponentSpecificDetails.vue";
import XMLContainer from "@/components/layout/XMLContainer.vue";

/*
 * Component to display detailed information about the selected SBML Component.
 */
export default defineComponent({
    components: {
        sbase: SBase,
        "component-specific-details": ComponentSpecificDetails,
        "xml-container": XMLContainer,
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
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/DetailContainer.scss";
</style>
