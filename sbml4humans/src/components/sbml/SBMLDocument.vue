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
        <div class="label">Models:</div>
        <div class="links">
            <ul title="List of Models">
                <li v-for="model in listOfModels" v-bind:key="model.pk">
                    <span v-on:click="openComponent(model.pk)"
                        >{{ model.id }} ({{ model.name }})</span
                    >
                </li>
            </ul>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of SBMLDocument objects.
 */
export default defineComponent({
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
            const modelPKs = store.state.componentPKsMap.Model;

            let modelAnnotations: Array<Record<string, string>> = [];
            modelPKs.forEach((pk) => {
                modelAnnotations.push(
                    store.state.allObjectsMap[pk] as Record<string, string>
                );
            });

            return modelAnnotations;
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
