<template>
    <form @submit.prevent="getExample()">
        <button class="btn list-item" type="submit">
            {{ exampleName }}
        </button>
    </form>
</template>

<script>
import createStore from "@/store/index";

export default {
    props: {
        exampleName: {
            type: String,
            default: "Model Name",
        },
        exampleId: {
            type: String,
            default: "example-id",
        },
    },

    data() {
        return {
            loading: createStore.state.jsonReport,
        };
    },

    methods: {
        async getExample() {
            const payload = {
                exampleId: this.exampleId,
            };

            createStore.dispatch("fetchExampleReport", payload);
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/Example.scss";
</style>
