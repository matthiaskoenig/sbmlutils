<template>
    <div class="list-group">
        <example
            v-for="ex in examples"
            v-bind:key="ex.id"
            v-bind:exampleName="ex.name"
            v-bind:exampleId="ex.id"
        ></example>
    </div>
    <h5 v-if="loading">Loading</h5>
    <h5>{{ jsonReport }}</h5>
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
        loading(){
            return createStore.state.loading;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/ExamplesListContainer.scss";
</style>
