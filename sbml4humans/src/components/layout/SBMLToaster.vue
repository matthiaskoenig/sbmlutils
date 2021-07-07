<template>
    <div class="card shadow-sm" v-if="visible" v-on:click="showDetail">
        <div
            class="d-flex px-2 justify-content-between"
            v-bind:style="`background-color: ${color}`"
        >
            <div class="mr-3">
                <strong>{{ info.id }}</strong>
                {{ info.name ? "(" + info.name + ")" : "" }}
            </div>
            <div>
                <strong>{{ sbmlType }}</strong>
            </div>
        </div>
        <div v-if="info.metaId || info.sbo" class="px-2 py-0">
            <div class="d-flex justify-content-between">
                <span class="text-primary" v-if="info.metaId">
                    metaId:
                    <span v-if="info.metaId.length < 20">{{ info.metaId }}</span>
                    <span v-else>{{ info.metaId.substring(0, 20) + "..." }}</span>
                </span>
                <span v-if="info.sbo">{{ info.sbo }}</span>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import colors from "@/data/colorScheme";
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
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
        info: {
            type: Object,
            default: TYPES.SBMLDocument,
        },
        visible: {
            type: Boolean,
            default: true,
        },
        isModel: {
            type: Boolean,
            default: false,
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
        /**
         * Reactively returns the visibility of SBML components from Vuex state/localStorage.
         */
        visibility(): Record<string, unknown> {
            return store.state.visibility;
        },
    },

    methods: {
        /**
         * Updates the detailInfo in Vuex state/localStorage to this SBML component's info.
         */
        showDetail(): void {
            if (this.isModel) {
                store.dispatch("updateCurrentModel", this.info.pk);
            }
            store.dispatch("initializeHistoryStack", this.info.pk);
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Toaster.scss";
</style>
