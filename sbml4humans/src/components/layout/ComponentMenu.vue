<template>
    <div style="opacity: 1">
    <div class="p-ml-2 p-mt-3 menuheader">COMPONENTS</div>
    <PanelMenu :model="items">
        <template #item="{ item }">
            <div class="menuitem" v-on:click="focusTable(item.sbmlType)">
                <span class="button p-mr-2">
                    <font-awesome-icon
                        :icon="item.icon"
                        :fixedWidth="true"
                        :border="false"
                        size="1x"
                        color="white"
                    ></font-awesome-icon>
                </span>
                <span class="p-mr-2">
                    <strong>{{ item.sbmlType }}</strong> ({{ item.count }})
                </span>
            </div>
        </template>
    </PanelMenu>
    </div>
</template>

<script lang="ts">
import colors from "@/data/colorScheme";
import icons from "@/data/fontAwesome";
import store from "@/store";
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
        items(): Array<Record<string, unknown>> {
            let tables: Array<Record<string, unknown>> = [];

            const componentPKsMap: Record<string, Array<string>> = store.getters
                .componentPKsMap;

            for (let sbmlType in componentPKsMap) {
                if (componentPKsMap[sbmlType].length > 0) {
                    tables.push({
                        label: sbmlType,
                        sbmlType: sbmlType,
                        color: colors.componentColor[sbmlType],
                        icon: icons.icons[sbmlType],
                        count:
                            store.state.searchedSBasesCounts[sbmlType] !=
                            componentPKsMap[sbmlType].length
                                ? store.state.searchedSBasesCounts[sbmlType] +
                                  "/" +
                                  componentPKsMap[sbmlType].length
                                : componentPKsMap[sbmlType].length,
                    });
                }
            }

            return tables;
        },
    },
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/Menu.scss";
</style>
