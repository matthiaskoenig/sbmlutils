<template>
    <div class="tablet p-d-flex p-mr-3" v-on:click="showDetail">
        <div class="p-d-flex p-jc-between">
            <font-awesome-icon :icon="`${icon}`" class="p-mt-1 p-mr-1" />
            {{ id }}
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

        icon(): string {
            return icons.icons[this.sbmlType];
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/Toaster.scss";

.tablet {
    padding: 1px 0px;
    width: fit-content;
    cursor: pointer;
}
</style>
