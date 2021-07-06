<template>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-3">
                <table-list-view-toggle></table-list-view-toggle>
            </div>
            <div class="col-md-9">
                <detail-container></detail-container>
            </div>
        </div>
    </div>
</template>

<script>
import { defineComponent } from "vue";

/* Compartments */
import DetailContainer from "@/components/layout/DetailContainer";
import TableListViewToggle from  "@/components/layout/TableListViewToggle.vue";

/**
 * Component to hold all components to show the generated report.
 */
export default defineComponent({
    components: {
        "detail-container": DetailContainer,
        "table-list-view-toggle": TableListViewToggle,
    },
});
</script>

<style lang="scss" scoped>
</style>
