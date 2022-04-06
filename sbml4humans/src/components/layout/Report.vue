<template>
    <Splitter>
        <SplitterPanel
            :size="15"
            :min-size="10"
            style="background-color: #f6f6f6; overflow-y: scroll"
        >
            <OMEXTree />

            <div class="p-ml-2 p-mt-4 menuheader">SEARCH</div>
            <InputText
                :modelValue="searchQuery"
                ref="search-bar"
                placeholder="Search"
                type="text"
                style="height: 35px; width: 100%"
                v-if="['report', 'Report'].includes($route.name)"
                @input="updateSearchQuery"
            />

            <component-menu />
        </SplitterPanel>
        <SplitterPanel
            class="panel p-p-2"
            :size="65"
            :min-size="40"
            style="background-color: white"
        >
            <tables-container />
        </SplitterPanel>
        <SplitterPanel
            class="panel p-py-2 p-pl-2"
            :size="20"
            :min-size="10"
            style="background-color: #f6f6f6"
        >
            <detail-container />
        </SplitterPanel>
    </Splitter>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

import DetailContainer from "@/components/layout/DetailContainer.vue";
import TablesContainer from "@/components/layout/TablesContainer.vue";
import ComponentMenu from "@/components/layout/ComponentMenu.vue";
//import DocumentMenu from "@/components/layout/DocumentMenu.vue";
import OMEXTree from "@/components/layout/OMEXTree.vue";

/**
 * Component to hold all components to show the generated report.
 */
export default defineComponent({
    data() {
        return {
            searchQuery: "",
        };
    },

    components: {
        ComponentMenu,
        //DocumentMenu,
        DetailContainer,
        TablesContainer,
        OMEXTree,
    },

    computed: {
        coreComponents(): Array<Record<string, unknown>> {
            return store.getters.reportBasics;
        },

        currentDocumentLocation() {
            return store.state.currentDocumentLocation;
        },
    },
    methods: {
        /**
         * Updates the searchQuery in Vuex state/localStorage to the currently
         * searched string in the search box.
         */
        updateSearchQuery(e: Event): void {
            this.searchQuery = (e.target as HTMLInputElement).value;
            store.dispatch("updateSearchQuery", (e.target as HTMLInputElement).value);
        },

        resetSearchBar(): void {
            //const el = JSON.parse(JSON.stringify(this.$refs["search-bar"]));
            // const el = this.$refs["search-bar"] as HTMLInputElement;
            // console.log(el);
            // el.value = "";
            this.searchQuery = "";
        },
    },

    watch: {
        currentDocumentLocation: {
            handler(current, old) {
                if (current != old) {
                    this.resetSearchBar();
                }
            },
            deep: true,
            immediate: true,
        },
    },
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/Menu.scss";
.panel {
    overflow-y: scroll;
    //overflow-x: scroll;
    //height: 100%;
    width: 100%;
}
</style>
