<template>
    <div class="ml-auto">
        <ol>
            <i
                class="fa fa-arrow-circle-left mr-3"
                v-on:click="goBack()"
                v-bind:style="styleBack"
            ></i>
            <i
                class="fa fa-arrow-circle-right mr-3"
                v-on:click="goForward()"
                v-bind:style="styleForward"
            ></i>
        </ol>
    </div>
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
            store.dispatch("moveStackPointerBack");
        },

        goForward(): void {
            store.dispatch("moveStackPointerForward");
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

        styleBack(): string {
            let style = "color: ";

            style +=
                store.state.stackPointer === 0
                    ? "#A9A9A9;"
                    : "#000000; cursor: pointer;";

            return style;
        },

        styleForward(): string {
            let style = "color: ";
            style +=
                store.state.stackPointer === store.state.historyStack.length - 1
                    ? "#A9A9A9"
                    : "#000000; cursor: pointer;";

            return style;
        },
    },
});
</script>

<style lang="scss" scoped></style>
