<template>
    <div class="p-grid p-pt-2">
        <div class="p-col-fixed" style="width: 220px">
            <component-menu />
            <document-menu class="p-mt-5" />
        </div>
        <div class="p-col">
            <div class="grid">
                <div class="p-col-12 p-md-8 column">
                    <tables-container />
                </div>
                <div class="p-col-12 p-md-4 column">
                    <detail-container />
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

import DetailContainer from "@/components/layout/DetailContainer.vue";
import TablesContainer from "@/components/layout/TablesContainer.vue";
import ComponentMenu from "@/components/layout/ComponentMenu.vue";
import DocumentMenu from "@/components/layout/DocumentMenu.vue";

/**
 * Component to hold all components to show the generated report.
 */
export default defineComponent({
    components: {
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

<style lang="scss">
.column {
    border-left: 1px solid #bfbfbf;
    height: 90vh;
    overflow-y: scroll;
}
</style>
