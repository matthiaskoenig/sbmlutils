<template>
    <nav class="detail-nav" aria-label="breadcrumb">
        <ol class="breadcrumb">
            <i
                class="fa fa-arrow-circle-left mr-3"
                v-on:click="goBack()"
                v-bind:style="style"
            ></i>
            <li
                class="breadcrumb-item links"
                v-for="pk in componentBrowseHistory"
                v-bind:key="pk"
                v-on:click="showDetail(pk)"
            >
                {{ pk.substring(0, 20) }}
            </li>
        </ol>
    </nav>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

export default defineComponent({
    props: {
        // will be useful in implementing the tabs feature
        detailViewID: {
            type: Number,
            default: 0,
        },
    },

    methods: {
        goBack(): void {
            if (store.state.historyStack.length <= 1) {
                return;
            }
            store.dispatch("popFromHistoryStack");
        },

        showDetail(pk: string): void {
            while (
                store.state.historyStack[store.state.historyStack.length - 1] != pk
            ) {
                store.dispatch("popFromHistoryStack");
            }
        },
    },

    computed: {
        componentBrowseHistory(): Array<string> {
            const allObjectsMap = store.state.allObjectsMap as Record<
                string,
                Record<string, unknown>
            >;
            const historyStack = store.state.historyStack;

            let listOfIDs: Array<string> = [];
            historyStack.forEach((pk) => {
                listOfIDs.push(allObjectsMap[pk]["pk"] as string);
            });

            return listOfIDs;
        },

        style(): string {
            let style = "";

            style =
                "color: " +
                (this.componentBrowseHistory.length > 1 ? "#000000" : "#A9A9A9") +
                ";";

            style =
                style +
                "cursor: " +
                (this.componentBrowseHistory.length > 1 ? "pointer" : "arrow") +
                ";";

            return style;
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/DetailViewNav.scss";
</style>
