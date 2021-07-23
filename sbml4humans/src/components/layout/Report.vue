<template>
    <div class="container-fluid">
        <div class="report-container">
            <div class="left">
                <list-of-sbases></list-of-sbases>
            </div>
            <div class="middle">
                <tables-container></tables-container>
            </div>
            <div class="right">
                <detail-container></detail-container>
            </div>

            <!--<div
                class="detailHideButton"
                v-on:click="toggleDetailVisibility"
                :title="`${
                    detailVisibility ? 'Hide' : 'Show'
                } the component detail view`"
            >
                <i
                    :class="`fa fa-eye${detailVisibility ? '-slash' : ''}`"
                    aria-hidden="true"
                    style="color: white; font-size: 36px; margin: 5px 0px"
                ></i>
            </div>-->
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
    height: 85vh;
    display: flex;
}

.left {
    width: 15%;
    //max-width: 200px;
}

.middle {
    width: 55%;
    overflow-y: scroll;
}

.right {
    width: 30%;
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
