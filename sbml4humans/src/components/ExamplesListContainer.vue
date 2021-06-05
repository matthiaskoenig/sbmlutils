<template>
    <div class="container">
        <img class="logo" alt="SBML logo" src="@/assets/images/logo.png" />
        <h5>Choose from the below list of example SBML models to generate a report</h5>
        <div class="list-group">
            <example
                v-for="ex in examples"
                v-bind:key="ex.id"
                v-bind:exampleName="ex.name"
                v-bind:exampleId="ex.id"
            ></example>
        </div>
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
                    name: String,
                    id: String,
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
            return store.state.loading;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/ExamplesListContainer.scss";
</style>
