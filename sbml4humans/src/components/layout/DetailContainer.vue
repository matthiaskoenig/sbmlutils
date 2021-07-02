<template>
    <div class="detail-container">
        <div class="table-detail" v-if="info.table">
            <table-detail
                v-bind:sbmlType="info.sbmlType[0]"
                v-bind:info="info"
            ></table-detail>
        </div>
        <sbase v-bind:info="info" v-if="!info.table"></sbase>
        <component-specific-details
            v-bind:info="info"
            v-bind:sbmlType="info.sbmlType"
            v-if="!info.table"
        ></component-specific-details>
        <!-- XML container -->
        <xml-container
            v-if="info.xml && !info.table"
            v-bind:xml="info.xml"
        ></xml-container>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import SBase from "@/components/sbml/SBase.vue";
import ComponentSpecificDetails from "@/components/layout/ComponentSpecificDetails.vue";
import XMLContainer from "@/components/layout/XMLContainer.vue";
import TableDetail from "@/components/sbml/TableDetail.vue";

/*
 * Component to display detailed information about the selected SBML Component.
 */
export default defineComponent({
    components: {
        sbase: SBase,
        "component-specific-details": ComponentSpecificDetails,
        "xml-container": XMLContainer,
        "table-detail": TableDetail,
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
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/DetailContainer.scss";
</style>
