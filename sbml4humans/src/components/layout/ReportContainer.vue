<template>
    <div class="row">
        <div class="left-container">
            <search-and-filter ref="customization"></search-and-filter>
            <list-of-sbases ref="list"></list-of-sbases>
        </div>
        <div class="right-container">
            <detail-container></detail-container>
        </div>
    </div>
</template>

<script>
/* Compartments */
import SearchAndFilter from "@/components/layout/SearchAndFilter";
import ListOfSBases from "@/components/sbml/listOf/ListOfSBases";
import DetailContainer from "@/components/layout/DetailContainer";

/**
 * Component to hold all components to show the generated report.
 */
export default {
    components: {
        "search-and-filter": SearchAndFilter,
        "list-of-sbases": ListOfSBases,
        "detail-container": DetailContainer,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/ReportContainer.scss";
</style>
