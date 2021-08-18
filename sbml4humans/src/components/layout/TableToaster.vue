<template>
    <div class="p-card" v-if="visible" :title="'Navigate to ' + sbmlType">
        <div
            class="p-d-flex p-jc-between p-px-2 p-pt-2 p-pb-1"
            :style="`background-color: ${color}`"
        >
            <strong>
                <font-awesome-icon :icon="`${icon}`" class="p-mr-1" />
                {{ sbmlType === "Species" ? sbmlType : sbmlType + "s" }}</strong
            >
            <Badge :value="counts[sbmlType]" severity="info"></Badge>
        </div>
    </div>
</template>

<script lang="ts">
import colors from "@/data/colorScheme";
import icons from "@/data/fontAwesome";
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
        count: {
            type: Number,
            default: 0,
        },
        visible: {
            type: Boolean,
            default: true,
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

    computed: {
        icon(): string {
            return icons.icons[this.sbmlType];
        },

        /**
         * Reactively returns the count of each SBML component from Vuex state/localStorage.
         */
        counts(): Record<string, number> {
            return store.getters.counts;
        },

        /**
         * Reactively returns the visibility of each SBML component from Vuex state/localStorage.
         */
        visibility(): Record<string, boolean> {
            return store.state.visibility as { [key: string]: boolean };
        },
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
@import "@/assets/styles/scss/Toaster.scss";
</style>
