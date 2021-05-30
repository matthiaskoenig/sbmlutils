<template>
    <div class="list-group">
        <example
            v-for="ex in examples"
            v-bind:key="ex.id"
            v-bind:exampleName="ex.name"
            v-bind:exampleId="ex.id"
        ></example>
    </div>
</template>

<script>
import examples from "@/data/examples";

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
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/ExamplesListContainer.scss";
</style>
