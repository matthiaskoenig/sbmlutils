<template>
    <div class="p-grid">
        <div class="p-col-12 p-lg-2">
            <search v-if="['Report', 'report'].includes($route.name)" />
            <list-of-tables class="tables-container" />

            <strong>Document & Models</strong>

            <SBML-toaster
                v-for="component in coreComponents"
                :key="component.pk"
                :sbmlType="component.sbmlType"
                :info="component"
            />
        </div>
        <div class="p-col-12 p-lg-7">
            <tables-container />
        </div>
        <div class="p-col-12 p-lg-3">
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
import SBMLToaster from "@/components/layout/SBMLToaster.vue";
import ListOfTables from "@/components/sbmlmisc/ListOfTables.vue";

/**
 * Component to hold all components to show the generated report.
 */
export default defineComponent({
    components: {
        DetailContainer,
        TablesContainer,
        Search,
        SBMLToaster,
        ListOfTables,
    },
    computed: {
        coreComponents(): Array<Record<string, unknown>> {
            return store.getters.reportBasics;
        },
    },
});
</script>

<style lang="scss" scoped>
</style>
