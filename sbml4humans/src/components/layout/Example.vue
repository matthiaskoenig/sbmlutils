<template>
    <div class="card shadow-sm" v-on:click="getExample()">
        <div
            class="d-flex px-2 justify-content-between"
            v-bind:style="`background-color: ${color}`"
        >
            <div>
                <strong>{{ sbmlType }}</strong>
            </div>
        </div>
        <div class="px-2">
            <h6 class="d-flex justify-content-between pt-1 text-dark">
                <div v-if="info.name">Name: {{ info.name }}</div>
                <div v-if="info.sbo">{{ info.sbo }}</div>
            </h6>
            <div class="d-flex justify-content-between text-primary py-0">
                <div v-if="info.metaId">Meta ID: {{ info.metaId }}</div>
                <div v-if="info.id">SID: {{ info.id }}</div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import colors from "@/data/colorScheme";
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "vue";

/**
 * Component to show meta information about an example Model in the list of examples.
 */
export default defineComponent({
    props: {
        sbmlType: {
            type: String,
            default: "Model",
        },
        info: {
            type: Object,
            default: TYPES.Model,
        },
    },

    data(): Record<string, unknown> {
        return {
            color: {
                type: String,
                default: "#FFFFFF",
            },
        };
    },

    mounted(): void {
        this.color = colors.componentColor[this.sbmlType];
    },

    methods: {
        getExample(): void {
            const payload = {
                exampleId: this.info.fetchId,
            };

            store.dispatch("fetchExampleReport", payload);
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Toaster.scss";
</style>
