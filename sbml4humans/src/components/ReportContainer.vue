<template>
    <div class="row">
        <div class="left-container">
            <list-of-sbases></list-of-sbases>
        </div>
        <div class="right-container">
            <detail-container></detail-container>
        </div>
    </div>
</template>

<script>
/* Compartments */
import ListOfSBases from "@/components/sbml/listOf/ListOfSBases";
import DetailContainer from "@/components/DetailContainer";

export default {
    components: {
        "list-of-sbases": ListOfSBases,
        "detail-container": DetailContainer,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/ReportContainer.scss";
</style>
