<template>
    <div class="card shadow-sm mr-3 small" v-on:click="showDetail">
        <div
            class="d-flex px-2 justify-content-between text-wrap"
            v-bind:style="`background-color: ${color}`"
        >
            <div class="mr-3">
                <strong>{{ id }}</strong>
            </div>
            <div>
                <strong>{{ sbmlType }}</strong>
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
        pk: {
            type: String,
            default: "",
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
            store.dispatch("pushToHistoryStack", this.pk);
        },
    },

    computed: {
        id(): string {
            const parts = this.pk.split(":");
            return parts[parts.length - 1];
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/Toaster.scss";
</style>
