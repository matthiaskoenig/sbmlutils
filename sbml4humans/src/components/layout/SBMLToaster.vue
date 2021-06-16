<template>
    <div class="card shadow-sm" v-if="visible" v-on:click="showDetail()">
        <div
            class="tag d-flex justify-content-between"
            v-bind:style="`background-color: ${color}`"
        >
            <div class="left-text">
                <strong>{{ sbmlType }}</strong>
            </div>
        </div>
        <div class="card-body">
            <h6 class="card-subtitle d-flex justify-content-between">
                <div class="name" v-if="info.name">Name: {{ info.name }}</div>
                <div class="sbo" v-if="info.sbo">{{ info.sbo }}</div>
            </h6>
            <div class="meta d-flex justify-content-between text-primary">
                <div v-if="info.metaId">
                    Meta ID:
                    <span v-if="info.metaId.length < 20">{{ info.metaId }}</span>
                    <span v-else>{{ info.metaId.substring(0, 20) + "..." }}</span>
                </div>
                <div v-if="info.id">
                    SID:
                    <span v-if="info.id.length < 20">{{ info.id }}</span>
                    <span v-else>{{ info.id.substring(0, 20) + "..." }}</span>
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import colors from "@/data/colorScheme";
import store from "@/store/index";
import TYPES from "@/sbmlComponents";

/**
 * Component to display meta data about an SBML objects.
 */
export default {
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
            store.dispatch("updateDetailInfo", this.info);
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/SBMLToaster.scss";
</style>
