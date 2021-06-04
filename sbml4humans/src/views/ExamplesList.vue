<template>
    <examples-container></examples-container>
</template>

<script lang="ts">
import { Vue, Options } from "vue-class-component";

/* Components */
import ExamplesListContainer from "@/components/ExamplesListContainer.vue";

@Options({
    components: {
        "examples-container": ExamplesListContainer,
    },
})
export default class ExamplesList extends Vue {}
</script>

<style lang="scss" scoped>

</style>
