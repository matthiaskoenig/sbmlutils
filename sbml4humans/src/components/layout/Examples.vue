<template>
    <div>
    <h1>Examples</h1>
    <DataView
        :value="examples"
        :layout="layout"
        :rows="4"
        :paginator="false"
    >
        <template #list="slotProps">
            <div class="p-col-12">
                <example :key="slotProps.data.id" :example="slotProps.data" />
            </div>
        </template>
    </DataView>
    <loading parent="example" />
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import Example from "@/components/layout/Example.vue";
import Loading from "@/components/layout/Loading.vue";

/**
 * Component to display list of all example models fetched from API.
 */
export default defineComponent({
    components: {
        Example,
        Loading,
    },
    data() {
        return {
            layout: "list",
        };
    },
    created(): void {
        store.dispatch("fetchExamples");
    },
    computed: {
        /**
         * Reactively returns the list of examples from Vuex state/localStorage.
         */
        examples(): Array<Record<string, unknown>> {
             return store.state.examples;
        },

        /**
         * Reactively returns the loading status of the example(s) from Vuex state/localStorage.
         */
        loading(): boolean {
            return store.state.exampleLoading;
        },
    },
});
</script>

<style lang="scss" scoped>
//.example-list {
//    height: 100%;
//}
//
//.p-orderlist-list-container {
//    height: auto !important;
//}
//
//.p-orderlist-controls {
//    display: none !important;
//    opacity: 0 !important;
//}
//
//.p-orderlist-item {
//    padding: 0 !important;
//    background-color: white;
//}
//
//.p-orderlist-item:hover {
//    padding: 0 !important;
//    background-color: white;
//}
//
//.p-orderlist-item:focus {
//    outline: none;
//}
//
//.p-orderlist-list {
//    border: none !important;
//    height: auto !important;
//}

</style>
