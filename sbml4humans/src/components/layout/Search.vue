<template>
    <div class="p-d-flex">
        <span class="p-input-icon-left" style="margin: 0 10px">
            <i class="pi pi-search" />
            <InputText
                type="text"
                @input="updateSearchQuery"
                placeholder="Search in SBML"
                style="width: 180px"
            />
        </span>
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
