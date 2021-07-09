<template>
    <div>
        <h1>Examples</h1>
        Choose from the below list of example SBML models to generate a report.
        <a-list class="list-container">
            <example
                v-for="example in examples"
                v-bind:key="example.id"
                v-bind:example="example"
            ></example>
        </a-list>
        <loading parent="example"></loading>
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
.list-container{
    overflow-y: scroll;
}
</style>
