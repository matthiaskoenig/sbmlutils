<template>

    <div class="search">
        <i class="fa fa-search px-2" style="color: black;"></i>
        <input
            class="form-control"
            type="text"
            placeholder="Search in SBML"
            @input="updateSearchQuery"
        />
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

/**
 * Component to make search queries on the SBML objectss present in the report.
 */
export default defineComponent({
    methods: {
        /**
         * Updates the searchQuery in Vuex state/localStorage to the currently searched string
         * in the search box.
         */
        updateSearchQuery(e: Event): void {
            store.dispatch("updateSearchQuery", (e.target as HTMLInputElement).value);
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Search.scss";
</style>
