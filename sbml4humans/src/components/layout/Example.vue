<template>
    <div
        class="card shadow-sm"
        v-on:click="getExample()"
        title="Click to create report for example"
    >
        <div
            class="d-flex px-2 justify-content-between"
            style="background-color: #66c2a5"
        >
            <div>
                <font-awesome-icon icon="file-code" class="mr-2" />
                <strong>{{ example.id }}</strong>
            </div>
        </div>
        <div class="px-2">
            <div><span class="text-primary">name</span>: {{ example.name }}</div>
            <div>
                <span class="text-primary">description</span>: {{ example.description }}
            </div>
            <div v-if="example.packages.length">
                <span class="text-primary">packages</span>:
                <span
                    v-for="pkg in example.packages"
                    :key="pkg"
                    :class="`badge badge-pill badge-${badgeColor[pkg]} package-badge mr-1`"
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
                distrib: "info",
                comp: "warning",
                fbc: "primary",
                groups: "success",
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
