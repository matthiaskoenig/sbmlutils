<template>
    <div class="detail-container">
        <!-- SBASE INFO -->
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
                info.sbmlType
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

        <br />

        <!-- COMPONENT SPECIFIC INFO -->
        <div ref="child"></div>
    </div>
</template>

<script>
import store from "@/store/index";
import Vue from "vue";

import { Compartment } from "@/components/sbml/Compartment";

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

    /*mounted() {
        console.log(this.info.sbmlType);
        if (this.info.sbmlType === "Compartment") {
            var ComponentClass = Vue.extend(Compartment);
            var componentInstance = new ComponentClass({
                propsData: {
                    info: this.info,
                },
            });
        }

        var childContainer = this.$refs.child;

        // remove existing elements in the component container
        if (childContainer.hasChildrenNodes) {
            while (childContainer.firstChild) {
                childContainer.removeChild(childContainer.firstChild);
            }
        }

        // inserting the new component in the container
        componentInstance.$mount();
        childContainer.child.appendChild(componentInstance.$el);
    },*/

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
