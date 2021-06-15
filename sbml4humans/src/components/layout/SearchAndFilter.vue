<template>
    <div class="customization-container">
        <div class="tab-menu">
            <!--<a-button class="collapser" shape="circle" icon="&uarr;" />-->
            <a-tabs default-active-key="1">
                <a-tab-pane class="tab-text" key="1" tab="Search">
                    <search-component></search-component>
                </a-tab-pane>
                <a-tab-pane
                    class="tab-text"
                    key="2"
                    v-bind:tab="`Filter ${filterFraction}`"
                >
                    <filter-component></filter-component>
                </a-tab-pane>
            </a-tabs>
        </div>
    </div>
</template>

<script>
import store from "@/store/index";

import Search from "@/components/layout/Search.vue";
import Filter from "@/components/layout/Filter.vue";

export default {
    components: {
        "search-component": Search,
        "filter-component": Filter,
    },

    computed: {
        visibility() {
            return store.state.visibility;
        },

        counts() {
            return store.state.counts;
        },

        allComponentsMap() {
            return store.state.componentPKsMap;
        },

        filterFraction() {
            let totalComponents = 0;
            let filteredComponents = 0;
            for (let component in this.counts) {
                totalComponents += this.counts[component];
                if (!this.visibility[component]) {
                    filteredComponents += this.counts[component];
                }
            }

            if (filteredComponents > 0) {
                return String("(" + filteredComponents + "/" + totalComponents + ")");
            }

            return "";
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/SearchAndFilter.scss";
</style>
