<template>
    <div class="card shadow-sm" v-if="visible" v-on:click="showDetail">
        <div
            class="tag d-flex justify-content-between"
            v-bind:style="`background-color: ${color}`"
        >
            <div class="left-right">
                <strong
                    >ListOf{{
                        sbmlType === "Species" ? sbmlType : sbmlType + "s"
                    }}</strong
                >
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import colors from "@/data/colorScheme";
import store from "@/store/index";
import { defineComponent } from "vue";

/**
 * Component to display meta data about an SBML objects.
 */
export default defineComponent({
    props: {
        sbmlType: {
            type: String,
            default: "SBMLDocument",
        },
        visible: {
            type: Boolean,
            default: true,
        },
        listOfPKs: {
            type: Array,
            default: Array,
        },
    },

    data(): Record<string, unknown> {
        return {
            color: {
                type: String,
                default: "#FFFFFF",
            },
        };
    },

    mounted(): void {
        this.color = colors.componentColor[this.sbmlType];
    },

    methods: {
        /**
         * Updates the detailInfo in Vuex state/localStorage to this SBML component's info.
         */
        showDetail(): void {
            store.dispatch("initializeHistoryStack", "ListOf" + this.sbmlType);
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Toaster.scss";
</style>
