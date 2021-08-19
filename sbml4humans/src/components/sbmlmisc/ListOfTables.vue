<template>
    <ScrollPanel style="width: 100%; height: 350px">
        <div
            class="p-d-flex p-card p-py-1 p-px-2 p-mb-2 clickable"
            :style="`background-color: ${table.color}`"
            v-for="table in collectTables"
            :key="table"
            v-on:click="focusTable(table.sbmlType)"
        >
            <font-awesome-icon
                :icon="table.icon"
                class="p-mr-2 p-mt-1"
            ></font-awesome-icon>
            <span class="p-mr-2"
                ><strong>{{ table.sbmlType }}</strong></span
            >
            <span class="p-ml-auto">
                <Badge :value="table.listOfPKs.length" severity="info"></Badge>
            </span>
        </div>
    </ScrollPanel>
</template>

<script lang="ts">
import colors from "@/data/colorScheme";
import icons from "@/data/fontAwesome";
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

export default defineComponent({
    methods: {
        focusTable(sbmlType: string) {
            store.dispatch("updateCurrentFocussedTable", sbmlType);
        },
    },

    computed: {
        /**
         * Collects and returns SBML objects present in the report and
         * applies search filtering on the response set.
         */
        collectTables(): Array<Record<string, unknown>> {
            let tables: Array<Record<string, unknown>> = [];

            const componentPKsMap: Record<string, Array<string>> = store.getters
                .componentPKsMap;

            for (let sbmlType in componentPKsMap) {
                if (componentPKsMap[sbmlType].length > 0) {
                    tables.push({
                        sbmlType: sbmlType,
                        color: colors.componentColor[sbmlType],
                        icon: icons.icons[sbmlType],
                        listOfPKs: componentPKsMap[sbmlType],
                    });
                }
            }

            return tables;
        },
    },
});
</script>

<style lang="scss" scoped>
.clickable {
    cursor: pointer;
}
</style>
