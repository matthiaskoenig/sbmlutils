<template>
    <div class="card shadow-sm" v-if="visible" v-on:click="showDetail">
        <div
            class="tag d-flex justify-content-between"
            v-bind:style="`background-color: ${color}`"
        >
            <div class="right-left">
                <strong>{{ info.id }}</strong>
                {{ info.name ? "(" + info.name + ")" : "" }}
            </div>
            <div class="left-right">
                <strong>{{ sbmlType }}</strong>
            </div>
        </div>
        <div v-if="info.metaId || info.sbo" class="card-body">
            <div class="d-flex justify-content-between">
                <span class="text-primary" v-if="info.metaId">
                    metaId:
                    <span v-if="info.metaId.length < 20">{{ info.metaId }}</span>
                    <span v-else>{{ info.metaId.substring(0, 20) + "..." }}</span>
                </span>
                <span class="sbo" v-if="info.sbo">{{ info.sbo }}</span>
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
            store.dispatch("initializeHistoryStack", this.info.pk);
            store.dispatch("updateDetailInfo", this.info);
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/SBMLToaster.scss";
</style>
