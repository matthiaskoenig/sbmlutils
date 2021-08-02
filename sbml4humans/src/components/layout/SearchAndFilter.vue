<template>
    <div class="search-filter-container d-flex w-50 mx-auto">
        <Search />
        <Filter />
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";

/* Components */
import Search from "@/components/layout/Search.vue";
import Filter from "@/components/layout/Filter.vue";

/**
 * Component to hold Search and Filter components.
 */
export default defineComponent({
    components: {
        Filter,
        Search,
    },
});
</script>

<style lang="scss" scoped></style>
