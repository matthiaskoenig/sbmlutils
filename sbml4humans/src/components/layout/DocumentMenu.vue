<template>
    <div style="opacity: 1">
        <div class="p-ml-2 p-mt-4 menuheader">MODELS</div>
        <div>
            <PanelMenu :model="coreComponents" style="width: 100%">
                <template #item="{ item }">
                    <div class="menuitem" @click="showDetail(item.sbmlType, item.pk)">
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
        </div>
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
@import "@/assets/styles/scss/Menu.scss";
</style>
