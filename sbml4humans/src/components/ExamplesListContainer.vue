<template>
    <div class="container">
        <h5>Choose from the below list of example SBML models to generate a report</h5>
        <a-list class="list-container">
            <example
                v-for="ex in examples"
                v-bind:key="ex.fetchId"
                v-bind:info="ex"
                sbmlType="Model"
            ></example>
        </a-list>
        <div class="loader" v-if="loading">
            <h6>Please wait...</h6>
            <span class="loading"><a-spin size="large" /></span>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";

/* Components */
import Example from "@/components/Example.vue";

export default {
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
        examples(): Array<Record<string, unknown>> {
            return store.state.examples;
        },
        loading(): boolean {
            return store.state.exampleLoading;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/ExamplesListContainer.scss";
</style>
