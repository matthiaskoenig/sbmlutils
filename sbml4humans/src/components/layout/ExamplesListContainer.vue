<template>
    <div class="container">
        <h1>Examples</h1>
        <p>Choose from the below list of example SBML models to generate a report.</p>
        <a-list class="list-container">
            <example
                v-for="ex in examples"
                v-bind:key="ex.fetchId"
                v-bind:info="ex"
                sbmlType="Model"
                title="Click to generate report for this model"
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
            msg: {
                type: String,
                default: "Loading Examples ...",
            },
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
