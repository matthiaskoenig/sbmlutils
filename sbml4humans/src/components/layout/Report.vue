<template>
    <div class="report-container">
        <div class="left">
            <div class="p-mb-3">
                <router-link to="/">
                    <div style="display: flex">
                        <img
                            alt="logo"
                            src="../../../public/sbmlutils-logo-60.png"
                            height="30"
                            width="80"
                            class="p-mr-2 p-mt-3"
                        />
                        <h4 class="brand">SBML4Humans</h4>
                    </div>
                </router-link>

                <search-and-filter
                    v-if="['Report', 'report'].includes($route.name)"
                ></search-and-filter>
            </div>

            <list-of-SBases />
        </div>
        <div class="middle">
            <tables-container />
        </div>
        <div class="right">
            <detail-container />
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

/* Compartments */
import DetailContainer from "@/components/layout/DetailContainer.vue";
import TablesContainer from "@/components/layout/TablesContainer.vue";
import ListOfSBases from "@/components/sbmlmisc/ListOfSBases.vue";
import SearchAndFilter from "@/components/layout/SearchAndFilter.vue";

/**
 * Component to hold all components to show the generated report.
 */
export default defineComponent({
    components: {
        DetailContainer,
        TablesContainer,
        ListOfSBases,
        SearchAndFilter,
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
.brand {
    color: rgb(54, 53, 53);
    font-weight: 500;
}

.logo {
    height: 30px;
    margin-right: 2px;
}

.report-container {
    height: 95vh;
    display: flex;
    padding: 0;
}

.left {
    width: 15%;
    margin-right: 10px;
}

.middle {
    width: 58%;
    overflow-y: scroll;
}

.right {
    width: 27%;
}
</style>
