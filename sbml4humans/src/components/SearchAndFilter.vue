<template>
    <div class="customization-container">
        <div class="tab-menu">
            <!--<a-button class="collapser" shape="circle" icon="&uarr;" />-->
            <a-tabs default-active-key="1">
                <a-tab-pane class="tab-text" key="1" tab="Search">
                    <search-component></search-component>
                </a-tab-pane>
                <a-tab-pane class="tab-text" key="2" tab="Filter">
                    <filter-component></filter-component>
                </a-tab-pane>
            </a-tabs>
        </div>
    </div>
</template>

<script>
import Search from "@/components/Search.vue";
import Filter from "@/components/Filter.vue";

export default {
    components: {
        "search-component": Search,
        "filter-component": Filter,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/SearchAndFilter.scss";
</style>
