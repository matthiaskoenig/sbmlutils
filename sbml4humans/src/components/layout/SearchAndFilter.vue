<template>
    <div class="search-filter-container p-d-flex w-100">
        <Search />
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";

/* Components */
import Search from "@/components/layout/Search.vue";

/**
 * Component to hold Search and Filter components.
 */
export default defineComponent({
    components: {
        Search,
    },
});
</script>

<style lang="scss" scoped></style>
