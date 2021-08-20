<template>
    <list-of-tables class="tables-container" />

    <strong>Document & Models</strong>
    <ScrollPanel class="basics-container">
        <SBML-toaster
            v-for="component in collectReportBasics"
            :key="component.pk"
            :sbmlType="component.sbmlType"
            :info="component"
        />
    </ScrollPanel>


</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

import SBMLToaster from "@/components/layout/SBMLToaster.vue";
import ListOfTables from "@/components/sbmlmisc/ListOfTables.vue";

export default defineComponent({
    components: {
        SBMLToaster,
        ListOfTables,
    },

    data() {
        return {
            expandedKeys: { "0": true, "1": true },
            reportBasics: [] as Array<Record<string, unknown>>,
            sbases: [] as Array<Record<string, unknown>>,
        };
    },

    computed: {
        collectReportBasics(): Array<Record<string, unknown>> {
            return store.getters.reportBasics;
        },
    },
});
</script>

<style lang="scss" scoped>
</style>
