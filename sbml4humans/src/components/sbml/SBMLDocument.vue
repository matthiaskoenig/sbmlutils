<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.packages != null">
                <td class="label-td"><div class="label">packages</div></td>
                <td>
                    <div v-if="info.packages.document != null">
                        <Tag
                            :value="
                                'SBML Level ' +
                                info.packages.document.level +
                                ' Version ' +
                                info.packages.document.version
                            "
                            :style="`background-color: black; color: white`"
                        ></Tag>
                    </div>
                    <div v-if="info.packages.plugins != null">
                        <div
                            v-for="plugin in info.packages.plugins"
                            :key="plugin.prefix + plugin.version"
                        >
                            <Tag
                                :value="plugin.prefix + '-v' + plugin.version"
                                :style="`background-color: ${
                                    badgeColor[plugin.prefix]
                                }; color: ${badgeText[plugin.prefix]}`"
                            ></Tag>
                        </div>
                    </div>
                </td>
            </tr>
            <tr v-if="listOfModels.length > 0">
                <td class="label-td"><div class="label">models</div></td>
                <td>
                    <div
                        class="p-d-flex p-jc-between"
                        v-for="model in listOfModels"
                        :key="model"
                    >
                        <SBMLLink :pk="model.pk" :sbmlType="String('Model')" />
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import SBMLLink from "@/components/layout/SBMLLink.vue";
import { FilterMatchMode, FilterOperator } from "primevue/api";

/**
 * Component to define display of SBMLDocument objects.
 */
export default defineComponent({
    components: {
        SBMLLink,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.SBMLDocument,
        },
    },
    data() {
        return {
            // [#a6cee3, #1f78b4, #b2df8a, #33a02c, #fb9a99, #e31a1c, #fdbf6f, #ff7f00, #cab2d6, #6a3d9a]
            badgeColor: {
                distrib: "#a6cee3",
                comp: "#1f78b4",
                fbc: "#b2df8a",
                groups: "#33a02c",
                layout: "#fb9a99",
                render: "#e31a1c",
            },

            badgeText: {
                distrib: "#000000",
                comp: "#ffffff",
                fbc: "#000000",
                groups: "#ffffff",
                layout: "#000000",
                render: "#ffffff",
            },
        };
    },
    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },

    computed: {
        listOfModels(): Array<Record<string, unknown>> {
            let reportBasics: Array<Record<string, unknown>> = [];
            (store.getters.reportBasics as Array<Record<string, unknown>>).forEach(
                (object) => {
                    if (object.sbmlType != "SBMLDocument") {
                        reportBasics.push(object);
                    }
                }
            );

            return reportBasics;
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
