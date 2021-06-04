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

<script>
import examples from "@/data/examples";
import createStore from "@/store/index";

/* Components */
import Example from "@/components/Example";

export default {
    components: {
        example: Example,
    },

    data() {
        return {
            examples: examples.listOfExamples,
        };
    },

    computed: {
        jsonReport() {
            return createStore.state.jsonReport;
        },
        loading() {
            return createStore.state.loading;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/ExamplesListContainer.scss";
</style>
