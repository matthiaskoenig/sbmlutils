<template>
    <a-list-item
        :key="`a-${sid}`"
        v-bind:style="`background-color: ${color};`"
        class="toaster"
    >
        <template #actions><a @click="showDetail()">View Details</a></template>
        <a-list-item-meta v-bind:description="`SID: ${sid}`">
            <template #title>
                <a href="#">{{ name }}</a>
            </template>
            <template #avatar>
                <a-tag color="success">{{ sbmlType }}</a-tag>
            </template>
        </a-list-item-meta>
    </a-list-item>
</template>

<script>
import colors from "@/data/colorScheme";
import store from "@/store/index";

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
            store.dispatch("updateDetailInfo", this.info);
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/SBMLToaster.scss";
</style>
