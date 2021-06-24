<template>
    <nav class="detail-nav" aria-label="breadcrumb">
        <ol class="breadcrumb">
            <i
                class="fa fa-arrow-circle-left mr-3"
                v-on:click="goBack()"
                v-bind:style="style"
            ></i>
            <li
                v-for="id in componentBrowseHistory"
                v-bind:key="id"
                class="breadcrumb-item links"
            >
                {{ id.substring(0, 20) }}
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
                (this.componentBrowseHistory.length > 1 ? "#000080" : "#A9A9A9") +
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
