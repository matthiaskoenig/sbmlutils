<template>
    <div style="opacity: 1">
        <div class="p-ml-2 p-mt-4 menuheader">COMPONENTS</div>
        <PanelMenu :model="coreComponents" style="width: 100%">
            <template #item="{ item }">
                <div
                    class="menuitem"
                    @click="showDetail(item.sbmlType, item.pk)"
                    v-if="item.sbmlType === 'SBMLDocument'"
                >
                    <span class="button p-mr-2">
                        <font-awesome-icon
                            :icon="item.icon"
                            :fixedWidth="true"
                            :border="false"
                            size="1x"
                            :color="item.color"
                        ></font-awesome-icon>
                    </span>
                    <span>
                        <strong>{{ item.sbmlType }}</strong>
                        <span v-if="item.id != null">{{ item.id }}</span>
                    </span>
                </div>
            </template>
        </PanelMenu>
        <PanelMenu :model="items">
            <template #item="{ item }">
                <div class="menuitem" v-on:click="focusTable(item.sbmlType)">
                    <span class="button p-mr-2">
                        <font-awesome-icon
                            :icon="item.icon"
                            :fixedWidth="true"
                            :border="false"
                            size="1x"
                            :color="item.color"
                        ></font-awesome-icon>
                    </span>
                    <span class="p-mr-2">
                        <strong>{{ item.sbmlType }}</strong> ({{ item.count }})
                    </span>
                </div>
            </template>
        </PanelMenu>
        <br />
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

        /**
         * Updates the detailInfo in Vuex state/localStorage to this SBML component's info.
         */
        showDetail(sbmlType: string, pk: string): void {
            if (sbmlType != "SBMLDocument") {
                store.dispatch("updateCurrentModel", pk);
            }
            store.dispatch("initializeHistoryStack", pk);
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
                if (
                    !sbmlType.includes("ModelDefinition") &&
                    componentPKsMap[sbmlType].length > 0
                ) {
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

        coreComponents(): Array<Record<string, unknown>> {
            const components: Array<Record<string, unknown>> = [];
            store.getters.reportBasics.forEach((component) => {
                components.push({
                    sbmlType: component.sbmlType,
                    color: colors.componentColor[component.sbmlType],
                    icon: icons.icons[component.sbmlType],
                    id: component.id,
                    pk: component.pk,
                    name: component.name,
                });
            });
            return components;
        },
    },
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/Menu.scss";
</style>
