<template>
    <h4>Choose from the below list of example SBML models to generate a report</h4>
    <examples-container></examples-container>
</template>

<script lang="ts">
import { Vue, Options } from "vue-class-component";

/* Components */
import ExamplesListContainer from "@/components/ExamplesListContainer.vue";

@Options({
    components: {
        'examples-container': ExamplesListContainer
    }
})

export default class ExamplesList extends Vue{

}
</script>
