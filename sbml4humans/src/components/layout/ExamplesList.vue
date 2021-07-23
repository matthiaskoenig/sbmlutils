<template>
    <h1 class="w-100">Examples</h1>
    <p>Choose from the list of examples to generate a report.</p>

    <a-list class="list-container">
        <example
            v-for="example in examples"
            :key="example.id"
            :example="example"
        ></example>
    </a-list>
    <loading parent="example"></loading>
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
        example: Example,
        loading: Loading,
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
.list-container {
    width: 90%;
    overflow-y: scroll;
}
</style>
