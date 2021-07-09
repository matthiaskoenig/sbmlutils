<template>
    <div class="card shadow-sm" v-on:click="getExample()">
        <div
            class="d-flex px-2 justify-content-between"
            style="background-color: #66c2a5"
        >
            <div>
                <strong>{{ example.id }}</strong>
            </div>
        </div>
        <div class="px-2">
            <div><span class="text-primary">name</span>: {{ example.name }}</div>
            <div><span class="text-primary">description</span>: {{
                    example.description
                }}</div>
            <div><span class="text-primary">packages</span>: {{ example.packages }}</div>
            <div><span class="text-primary">keywords</span>: {{ example.keywords }}</div>
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
