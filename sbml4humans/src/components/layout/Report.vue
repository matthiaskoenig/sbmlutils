<template>
    <div class="p-grid p-p-2">
<!--        <div class="p-col-12 p-lg-2">-->
        <div class="p-col-fixed" style="width: 200px">
            <search class="p-ml-2" v-if="['Report', 'report'].includes($route.name)" />
            <component-menu class="p-mt-2" style="opacity: 1" />
            <document-menu class="p-mt-5" style="opacity: 1" />
        </div>

        <div class="p-col-12 p-md-3 p-lg-3 column">
            <detail-container />
        </div>
        <div class="p-col-12 p-md-7 p-lg-7 column">
            <tables-container />
        </div>

        <!--
        <div class="p-col-12 p-lg-10 column">
        <Splitter>
            <SplitterPanel :size="65" :minSize="50">
                <tables-container />
            </SplitterPanel>
            <SplitterPanel :size="35" :minSize="10">
                <detail-container />
            </SplitterPanel>
        </Splitter>
        </div>
        -->

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

<style lang="scss">
.column {
    border-left: 1px solid #bfbfbf;
    height: 90vh;
    overflow-y: scroll;
}
</style>
