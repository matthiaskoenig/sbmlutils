<template>
    <div
        class="p-card shadow-sm"
        v-on:click="getExample()"
        title="Click to create report for example"
    >
        <div class="p-d-flex p-px-2 p-jc-between" style="background-color: #66c2a5">
            <div>
                <font-awesome-icon icon="file-code" class="p-mr-2" />
                <strong>{{ example.id }}</strong>
            </div>
        </div>
        <div class="p-px-2">
            <div><span class="text-primary">name</span>: {{ example.name }}</div>
            <div>
                <span class="text-primary">description</span>: {{ example.description }}
            </div>
            <div v-if="example.packages.length">
                <span class="text-primary">packages</span>:
                <span
                    v-for="pkg in example.packages"
                    :key="pkg"
                    :class="`package-badge p-mr-1`"
                    :style="`background-color: ${badgeColor[pkg]}; color: ${badgeText[pkg]}`"
                    >{{ pkg }}</span
                >
            </div>
            <div>
                <span class="text-primary">keywords</span>:
                {{ example.keywords.join(",") }}
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "vue";

/**
 * Component to show meta information about an example Model in the list of examples.
 */
export default defineComponent({
    props: {
        example: {
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

            badgeColor: {
                distrib: "#5bc0de",
                comp: "#f0ad4e",
                fbc: "#0275d8",
                groups: "#5cb85c",
            },

            badgeText: {
                distrib: "#000000",
                comp: "#000000",
                fbc: "#ffffff",
                groups: "#ffffff",
            },
        };
    },
    methods: {
        getExample(): void {
            const payload = {
                exampleId: this.example.id,
            };

            store.dispatch("fetchExampleReport", payload);
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/Toaster.scss";
</style>
