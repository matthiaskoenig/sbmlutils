<template>
    <span class="p-input-icon-left">
        <i class="pi pi-search"/>
        <InputText
            type="text"
            @input="updateSearchQuery"
            placeholder="Search in SBML"
        />
    </span>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

export default defineComponent({
    methods: {
        /**
         * Updates the searchQuery in Vuex state/localStorage to the currently
         * searched string in the search box.
         */
        updateSearchQuery(e: Event): void {
            store.dispatch("updateSearchQuery", (e.target as HTMLInputElement).value);
        },
    },
});
</script>

<style lang="scss" scoped></style>
