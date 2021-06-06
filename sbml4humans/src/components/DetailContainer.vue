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

<script>
import store from "@/store/index";

import SBase from "@/components/sbml/SBase.vue";
import ComponentSpecificDetails from "@/components/ComponentSpecificDetails.vue";

export default {
    components: {
        sbase: SBase,
        "component-specific-details": ComponentSpecificDetails,
    },

    data() {
        return {
            sbmlType: String,
        };
    },

    computed: {
        info: {
            get() {
                return store.state.detailInfo;
            },
        },
    },

    watch: {
        info() {
            this.sbmlType = store.state.detailInfo.sbmlType;
            this.infoData = store.state.detailInfo;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/DetailContainer.scss";
</style>
