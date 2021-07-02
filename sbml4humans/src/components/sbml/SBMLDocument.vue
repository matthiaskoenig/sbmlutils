<template>
    <!-- Package Information -->
    <div class="data" v-if="info.packages">
        <div class="label">
            <strong>packages: </strong>
            <div class="ml-4" v-if="info.packages.document">
                document: Level {{ info.packages.document.level }} Version
                {{ info.packages.document.version }}
            </div>
            <div class="ml-4" v-if="info.packages.plugins">
                plugins:
                <ul class="ml-4" title="List of Plugins">
                    <li
                        v-for="plugin in info.packages.plugins"
                        v-bind:key="plugin.prefix + plugin.version"
                    >
                        prefix: {{ plugin.prefix }}, version: {{ plugin.version }}
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <!-- List of Models -->
    <div class="data" v-if="listOfModels.length > 0">
        <div class="label"><strong>models:</strong></div>
        <div class="ml-4">
            <div
                class="ml-4 d-flex justify-content-between"
                v-for="model in listOfModels"
                v-bind:key="model"
            >
                <SBMLLink
                    v-bind:pk="model.pk"
                    v-bind:sbmlType="String('Model')"
                ></SBMLLink>
            </div>
        </div>
    </div>
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
        listOfModels(): Array<Record<string, string>> {
            return store.getters.reportBasics;
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
