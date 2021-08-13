<template>
    <div class="d-flex">
        <font-awesome-icon icon="search" class="mx-2 mt-2" />
        <input
            class="form-control"
            type="text"
            placeholder="Search in SBML"
            @input="updateSearchQuery"
            style="font-size: small"
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

<style lang="scss" scoped></style>
