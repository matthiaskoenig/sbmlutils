<template>
    <div class="container">
        <a-descriptions
            bordered
            v-bind:title="`${info.name} - ${info.sbo}`"
            :size="size"
        >
            <a-descriptions-item label="Name">{{ info.name }}</a-descriptions-item>
            <a-descriptions-item label="SID">{{ info.id }}</a-descriptions-item>
            <a-descriptions-item label="SBO">{{ info.sbo }}</a-descriptions-item>
            <a-descriptions-item label="Meta ID">{{ info.metaId }}</a-descriptions-item>
            <a-descriptions-item label="SBML Type">{{
                info.sbaseType
            }}</a-descriptions-item>
            <a-descriptions-item label="XML">
                <a-button type="info" @click="showModal">View Source</a-button>
                <a-modal
                    v-model:visible="visible"
                    width="1000px"
                    v-bind:title="`${info.name} - ${info.sbo}`"
                    v-bind:footer="null"
                    @ok="handleOk"
                >
                    <p>{{ info.xml }}</p>
                </a-modal>
            </a-descriptions-item>
        </a-descriptions>
    </div>
</template>

<script>
import store from "@/store/index";
import vkbeautify from "vkbeautify";

import { ref } from "vue";

export default {
    data() {
        return {
            visible: false,
        };
    },

    computed: {
        info() {
            return store.state.detailInfo;
        },
    },

    mounted() {
        this.info = store.state.info;
    },

    methods: {
        showModal() {
            this.visible = true;
        },

        handleOk() {
            this.visible = false;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/DetailContainer.scss";
</style>
