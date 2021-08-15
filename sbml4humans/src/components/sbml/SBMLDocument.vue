<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.packages != null">
                <td class="label-td"><div class="label">packages</div></td>
                <td>
                    <div v-if="info.packages.document != null">
                        document: Level {{ info.packages.document.level }} Version
                        {{ info.packages.document.version }}
                    </div>
                    <div v-if="info.packages.plugins != null">
                        plugins:
                        <ul title="List of Plugins">
                            <li
                                v-for="plugin in info.packages.plugins"
                                :key="plugin.prefix + plugin.version"
                            >
                                prefix: {{ plugin.prefix }}, version:
                                {{ plugin.version }}
                            </li>
                        </ul>
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

    <!-- <div class="data" v-if="info.packages != null">
        <div class="label">
            <strong>packages: </strong>
            <div class="p-ml-4" v-if="info.packages.document != null">
                document: Level {{ info.packages.document.level }} Version
                {{ info.packages.document.version }}
            </div>
            <div class="p-ml-4" v-if="info.packages.plugins != null">
                plugins:
                <ul class="p-ml-4" title="List of Plugins">
                    <li
                        v-for="plugin in info.packages.plugins"
                        :key="plugin.prefix + plugin.version"
                    >
                        prefix: {{ plugin.prefix }}, version: {{ plugin.version }}
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <div class="data" v-if="listOfModels.length > 0">
        <div class="label"><strong>models:</strong></div>
        <div class="p-ml-4">
            <div
                class="p-ml-4 p-d-flex p-jc-between"
                v-for="model in listOfModels"
                :key="model"
            >
                <SBMLLink :pk="model.pk" :sbmlType="String('Model')" />
            </div>
        </div>
    </div> -->
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import SBMLLink from "@/components/layout/SBMLLink.vue";

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
