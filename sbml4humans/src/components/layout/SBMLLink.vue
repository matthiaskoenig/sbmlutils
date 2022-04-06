<template>
    <Tag
        class="tablet p-mr-1 p-mt-1"
        v-on:click="showDetail"
        :rounded="true"
        style="background-color: lightgrey; color: black"
    >
        <font-awesome-icon :icon="`${icon}`" /><span class="p-ml-1">{{ id }}</span>
    </Tag>
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
//@import "@/assets/styles/scss/Toaster.scss";

.tablet {
    //padding: 1px 0px;
    //width: fit-content;
    cursor: pointer;
}
</style>
