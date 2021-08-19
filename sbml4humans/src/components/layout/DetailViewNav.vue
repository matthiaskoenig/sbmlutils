<template>
    <div class="detailNav p-mr-3">
        <span :style="styleBack" class="p-mr-2">
            <font-awesome-icon
                icon="arrow-left"
                v-on:click="goBack()"
                style="
                    font-size: 16px;
                    border: 2px solid black;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    padding: 2%;
                    background-color: black;
                    color: white;
                "
            ></font-awesome-icon>
        </span>
        <span :style="styleForward">
            <font-awesome-icon
                icon="arrow-right"
                v-on:click="goForward()"
                style="
                    font-size: 16px;
                    border: 2px solid black;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    padding: 2%;
                    background-color: black;
                    color: white;
                "
            ></font-awesome-icon>
        </span>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

export default defineComponent({
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

<style lang="scss" scoped>
.detailNav {
    position: fixed;
    width: max-content;
    padding: 0;
    right: 10px;

    z-index: 50;
}

.fa {
    background-color: white;
    border-radius: 12px;
}
</style>
