<template>
    <div class="container-fluid">
        <div class="report-container">
            <div class="left">
                <!--<table-list-view-toggle></table-list-view-toggle>-->
                <list-of-sbases></list-of-sbases>
            </div>
            <div class="right">
                <tables-container></tables-container>
            </div>
            <detail-container></detail-container>
            <div
                class="detailHideButton"
                v-on:click="toggleDetailVisibility"
                v-bind:title="`${
                    detailVisibility ? 'Hide' : 'Show'
                } the component detail view`"
            >
                <i
                    v-bind:class="`fa fa-eye${detailVisibility ? '-slash' : ''}`"
                    aria-hidden="true"
                    style="color: white; font-size: 36px; margin: 5px 0px"
                ></i>
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

/**
 * Component to hold all components to show the generated report.
 */
export default defineComponent({
    components: {
        "detail-container": DetailContainer,
        "tables-container": TablesContainer,
        "list-of-sbases": ListOfSBases,
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
.report-container {
    height: 80vh;
    display: flex;
}

.left {
    width: 20%;
    margin-right: 2%;
}

.right {
    width: 78%;
    overflow-y: scroll;
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
