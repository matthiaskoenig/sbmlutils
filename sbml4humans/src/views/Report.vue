<template>
    <report-container></report-container>
</template>

<script lang="ts">
import { Vue, Options } from "vue-class-component";

/* Components */
import ReportContainer from "@/components/ReportContainer.vue";

@Options({
    components: {
        "report-container": ReportContainer,
    },
})
export default class ExamplesList extends Vue {}
</script>
