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

<script lang="ts">
import store from "@/store/index";

/* Components */
import Search from "@/components/layout/Search.vue";
import Filter from "@/components/layout/Filter.vue";

/**
 * Component to hold Search and Filter components.
 */
export default {
    components: {
        "search-component": Search,
        "filter-component": Filter,
    },

    computed: {
        /**
         * Reactively returns the visibility of each SBML component from Vuex state/localStorage.
         */
        visibility(): Record<string, boolean> {
            return store.state.visibility;
        },

        /**
         * Reactively returns the count of each SBML component from Vuex state/localStorage.
         */
        counts(): Record<string, number> {
            return store.state.counts;
        },

        /**
         * Calculates and displays the fraction of SBML objects filtered in the report.
         */
        filterFraction(): string {
            let totalComponents = 0;
            let filteredComponents = 0;

            // calulating the total SBML objects and the number of filtered objects.
            for (let component in this.counts) {
                totalComponents += this.counts[component];
                if (!this.visibility[component]) {
                    filteredComponents += this.counts[component];
                }
            }

            // show the filter fraction only if some objects have been actually filtered
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
