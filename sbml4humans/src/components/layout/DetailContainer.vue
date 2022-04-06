<template>
    <div ref="detailContainer" class="detail-container">
        <!-- Back and Forward Buttons -->
        <!-- FIXME <detail-view-nav /> -->

        <!-- SBase Information -->
        <SBase :info="info" />

        <!-- Per SBML Component Information -->
        <component-specific-details :info="info" :sbmlType="info.sbmlType" />

        <!-- Additional Information for the component -->
        <additional-data :info="info" />
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import SBase from "@/components/sbml/SBase.vue";
import ComponentSpecificDetails from "@/components/layout/ComponentSpecificDetails.vue";
import DetailViewNav from "@/components/layout/DetailViewNav.vue";
import AdditionalData from "@/components/layout/AdditionalData.vue";

/*
 * Component to display detailed information about the selected SBML Component.
 */
export default defineComponent({
    components: {
        SBase,
        ComponentSpecificDetails,
        //DetailViewNav,
        AdditionalData,
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

    watch: {
        info: {
            handler() {
                const el = this.$refs["detailContainer"] as HTMLDivElement;
                if (el) {
                    el.scrollTop = 0;
                }
            },
            deep: true,
            immediate: true,
        },
    },
});
</script>

<style lang="scss" scoped>
.detail-container {
    //word-wrap: break-word;
    overflow-y: scroll;
    overflow-x: scroll;
    font-size: smaller;
    height: 100%;
    width: 100%;
}
</style>
