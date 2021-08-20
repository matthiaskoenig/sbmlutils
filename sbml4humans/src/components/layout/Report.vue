<template>
    <div class="p-grid">
        <div class="p-col-12 p-lg-2">
            <search v-if="['Report', 'report'].includes($route.name)" />
            <list-of-s-bases />
        </div>
        <div class="p-col-12 p-lg-7">
            <tables-container />
        </div>
        <div class="p-col-12 p-lg-3">
            <detail-container />
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

import DetailContainer from "@/components/layout/DetailContainer.vue";
import TablesContainer from "@/components/layout/TablesContainer.vue";
import ListOfSBases from "@/components/sbmlmisc/ListOfSBases.vue";
import Search from "@/components/layout/Search.vue";

/**
 * Component to hold all components to show the generated report.
 */
export default defineComponent({
    components: {
        DetailContainer,
        TablesContainer,
        ListOfSBases,
        Search,
    },

    methods: {
        toggleDetailVisibility(): void {
            store.dispatch("toggleDetailVisibility");
        },
    },

    computed: {
        detailVisibility(): boolean {
            return store.state.detailVisibility;
        },
    },
});
</script>

<style lang="scss" scoped>
</style>
