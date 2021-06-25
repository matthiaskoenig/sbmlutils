<template>
    <div class="row">
        <div class="left-container">
            <list-of-sbases ref="list"></list-of-sbases>
        </div>
        <div class="right-container">
            <detail-view-nav></detail-view-nav>
            <detail-container></detail-container>
        </div>
    </div>
</template>

<script>
import { defineComponent } from "vue";

/* Compartments */
import ListOfSBases from "@/components/sbml/listOf/ListOfSBases";
import DetailContainer from "@/components/layout/DetailContainer";
import DetailViewNav from "@/components/layout/DetailViewNav.vue";

/**
 * Component to hold all components to show the generated report.
 */
export default defineComponent({
    components: {
        "list-of-sbases": ListOfSBases,
        "detail-container": DetailContainer,
        "detail-view-nav": DetailViewNav,
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/ReportContainer.scss";
</style>
