<template>
    <div class="container">
        <h1>Examples</h1>
        <p>
            Choose from the below list of example SBML models to generate a report.
        </p>
        <a-list class="list-container">
            <example
                v-for="ex in examples"
                v-bind:key="ex.fetchId"
                v-bind:info="ex"
                sbmlType="Model"
                title="Click to generate report for this model"
            ></example>
        </a-list>
        <div class="loader" v-if="loading">
            <h6>Report is being generated...</h6>
            <span class="loading"><a-spin size="large" /></span>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import Example from "@/components/layout/Example.vue";

/**
 * Component to display list of all example models fetched from API.
 */
export default defineComponent({
    components: {
        example: Example,
    },

    data(): Record<string, unknown> {
        return {
            listOfExamples: [
                {
                    fetchId: String,
                    name: String,
                    id: String,
                    sbo: String,
                    metaId: String,
                },
            ],
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
@import "@/assets/styles/scss/components/layout/ExamplesListContainer.scss";
</style>
