<template>
    <div class="card shadow-sm" v-if="visible">
        <div
            class="d-flex justify-content-between px-2"
            :style="`background-color: ${color}`"
        >
            <strong>
                <i :class="`fas fa-${icon} mr-1`"></i>
                {{ sbmlType === "Species" ? sbmlType : sbmlType + "s" }}</strong
            >
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
