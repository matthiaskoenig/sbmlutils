<template>
    <div class="search">
        <input
            class="form-control"
            type="text"
            placeholder="&nbsp; &#128270; &nbsp; Search for an SBML Component"
            @input="updateSearchQuery"
        />
    </div>
</template>

<script lang="ts">
import store from "@/store/index";

/**
 * Component to make search queries on the SBML objectss present in the report.
 */
export default {
    methods: {
        /**
         * Updates the searchQuery in Vuex state/localStorage to the currently searched string
         * in the search box.
         */
        updateSearchQuery(e: Event): void {
            store.dispatch("updateSearchQuery", (e.target as HTMLInputElement).value);
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Search.scss";
</style>
