<template>
    <div class="card shadow-sm" v-on:click="showDetail()">
        <div
            class="tag d-flex justify-content-between"
            v-bind:style="`background-color: ${color}`"
        >
            <div class="left-text">
                <strong>{{ info.sbmlType }}</strong>
            </div>
            <div class="right-text">{{ info.sbo }}</div>
        </div>
        <div class="card-body">
            <h6 class="card-subtitle" v-if="info.name">Name: {{ info.name }}</h6>
            <div class="card-meta d-flex justify-content-between text-primary">
                <div v-if="info.metaId">Meta ID: {{ info.metaId }}</div>
                <div v-if="info.id">SID: {{ info.id }}</div>
            </div>
        </div>
    </div>
</template>

<script>
import colors from "@/data/colorScheme";
import store from "@/store/index";
import TYPES from "@/sbmlComponents";

export default {
    props: {
        sid: String,
        name: String,
        sbmlType: String,
        info: {},
    },

    data() {
        return {
            color: String,
        };
    },

    mounted() {
        this.color = colors.componentColor[this.sbmlType]
            ? colors.componentColor[this.sbmlType]
            : colors.componentColor.Default;
    },

    methods: {
        showDetail() {
            console.log("here at 55");
            store.dispatch("updateDetailInfo", this.info);
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/SBMLToaster.scss";
</style>
