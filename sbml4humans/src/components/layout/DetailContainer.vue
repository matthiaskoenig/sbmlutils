<template>
    <div class="detail-container">
        <!-- Back and Forward Buttons -->
        <detail-view-nav />

        <!-- SBase Information -->
        <sbase :info="info" />

        <!-- Per SBML Component Information -->
        <component-specific-details :info="info" :sbmlType="info.sbmlType" />

        <!-- JSON data about the SBML Component -->
        <JSONContainer v-if="info" :json="info" />

        <!-- XML Code of the SBML Component -->
        <XMLContainer v-if="info.xml" :xml="info.xml" />

    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import SBase from "@/components/sbml/SBase.vue";
import ComponentSpecificDetails from "@/components/layout/ComponentSpecificDetails.vue";
import XMLContainer from "@/components/layout/XMLContainer.vue";
import JSONContainer from "@/components/layout/JSONContainer.vue";
import DetailViewNav from "@/components/layout/DetailViewNav.vue";

/*
 * Component to display detailed information about the selected SBML Component.
 */
export default defineComponent({
    components: {
        Sbase: SBase,
        ComponentSpecificDetails,
        XMLContainer,
        JSONContainer,
        DetailViewNav,
    },

    computed: {
        /**
         * Reactively returns the detailInfo from Vuex state/localStorage.
         */
        info(): Record<string, unknown> {
            const detailInfo =
                store.state.allObjectsMap[
                    store.state.historyStack[store.state.stackPointer]
                ];

            return detailInfo;
        },

        visibility(): boolean {
            return store.state.detailVisibility;
        },
    },
});
</script>

<style lang="scss" scoped>
.detail-container {
    height: 85vh;
    padding: 10px 15px;

    word-wrap: break-word;
    overflow-y: scroll;
    overflow-x: scroll;

    background-color: white;
}
</style>
