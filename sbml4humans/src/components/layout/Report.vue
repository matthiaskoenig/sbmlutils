<template>
    <div class="container-fluid">
        <div class="report-container">
            <div class="left">
                <div class="navbar">
                    <router-link class="navbar-brand" to="/">
                        <img class="logo" src="@/assets/images/sbmlutils-logo-60.png" />
                        SBML4Humans
                    </router-link>

                    <!-- Search and Filter component (visible only in report view) -->
                    <search-and-filter
                        class="mt-2"
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
.navbar {
    margin-bottom: 10%;
    padding: 0;
}

.navbar-brand {
    color: black;
}

.logo {
    height: 30px;
    margin-right: 2px;
}

.report-container {
    height: 100vh;
    display: flex;
}

.left {
    width: 15%;
    margin-right: 10px;
    padding-top: 10px;
}

.middle {
    width: 58%;
    overflow-y: scroll;
    padding-top: 10px;
}

.right {
    width: 27%;
    padding-top: 10px;
}

.detailHideButton {
    position: absolute;
    width: 50px;
    height: 50px;
    bottom: 20px;
    right: 30px;

    text-align: center;

    border-radius: 25px;
    background-color: #5bc0de;
    cursor: pointer;

    z-index: 100;
}
</style>
