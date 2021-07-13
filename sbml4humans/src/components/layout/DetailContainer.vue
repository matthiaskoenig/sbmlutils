<template>
    <div class="detail-container shadow-lg col-md-5" v-if="visibility">
        <detail-view-nav></detail-view-nav>
        <sbase v-bind:info="info"></sbase>
        <component-specific-details
            v-bind:info="info"
            v-bind:sbmlType="info.sbmlType"
        ></component-specific-details>
        <!-- XML container -->
        <xml-container v-if="info.xml" v-bind:xml="info.xml"></xml-container>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import SBase from "@/components/sbml/SBase.vue";
import ComponentSpecificDetails from "@/components/layout/ComponentSpecificDetails.vue";
import XMLContainer from "@/components/layout/XMLContainer.vue";
import DetailViewNav from "@/components/layout/DetailViewNav.vue";

/*
 * Component to display detailed information about the selected SBML Component.
 */
export default defineComponent({
    components: {
        sbase: SBase,
        "component-specific-details": ComponentSpecificDetails,
        "xml-container": XMLContainer,
        "detail-view-nav": DetailViewNav,
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
    position: absolute;
    height: 85vh;
    right: 15px;
    padding: 15px 15px;

    word-wrap: break-word;
    overflow-y: scroll;

    background-color: white;
}
</style>
