<template>
    <div class="p-grid p-p-2">
        <div class="p-col-12 p-lg-2">
            <search v-if="['Report', 'report'].includes($route.name)" />
            <component-menu class="p-mt-2" />
            <document-menu class="p-mt-5" />
        </div>
        <div class="p-col-12 p-lg-7 middle">
            <tables-container />
        </div>
        <div class="p-col-12 p-lg-3 middle">
            <detail-container />
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

import DetailContainer from "@/components/layout/DetailContainer.vue";
import TablesContainer from "@/components/layout/TablesContainer.vue";
import Search from "@/components/layout/Search.vue";
import ComponentMenu from "@/components/layout/ComponentMenu.vue";
import DocumentMenu from "@/components/layout/DocumentMenu.vue";

/**
 * Component to hold all components to show the generated report.
 */
export default defineComponent({
    components: {
        Search,
        ComponentMenu,
        DocumentMenu,
        DetailContainer,
        TablesContainer,
    },

    computed: {
        coreComponents(): Array<Record<string, unknown>> {
            return store.getters.reportBasics;
        },
    },
});
</script>

<style lang="scss" scoped>
.middle {
    border-right: 1px solid #bfbfbf;
    height: 89vh;
    overflow-y: scroll;
}
</style>
