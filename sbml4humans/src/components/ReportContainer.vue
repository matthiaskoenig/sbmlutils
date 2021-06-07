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
import SearchAndFilter from "@/components/SearchAndFilter";
import ListOfSBases from "@/components/sbml/listOf/ListOfSBases";
import DetailContainer from "@/components/DetailContainer";

export default {
    components: {
        "search-and-filter": SearchAndFilter,
        "list-of-sbases": ListOfSBases,
        "detail-container": DetailContainer,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/ReportContainer.scss";
</style>
