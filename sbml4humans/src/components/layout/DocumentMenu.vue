<template>
    <div>
        <h3 class="p-ml-2">Document & Models</h3>

        <PanelMenu :model="coreComponents">
            <template #item="{ item }">
                <div class="clickable" @click="showDetail(item.sbmlType, item.pk)">
                    <div>
                        <span :style="`color: ${item.color}`">
                            <font-awesome-icon
                                :icon="item.icon"
                                :fixedWidth="true"
                                :border="false"
                                size="1x"
                                class="p-mr-2"
                            ></font-awesome-icon>
                        </span>
                        <span class="p-mr-2">
                            <strong>{{ item.sbmlType }}</strong>
                        </span>
                    </div>
                    <div class="p-ml-1">
                        <span v-if="item.id != null"> id: {{ item.id }}</span>
                    </div>
                </div>
            </template>
        </PanelMenu>
    </div>
</template>

<script lang="ts">
import store from "@/store";
import colors from "@/data/colorScheme";
import icons from "@/data/fontAwesome";
import { defineComponent } from "@vue/runtime-core";

export default defineComponent({
    methods: {
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

<style lang="scss" scoped>
.clickable {
    padding: 8px;
    cursor: pointer;
}

.clickable:hover {
    cursor: pointer;
    background-color: #dfdfdf;
}
</style>
