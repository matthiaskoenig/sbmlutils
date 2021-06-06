<template>
    <div class="detail-container">
        <!-- SBASE INFO -->
        <div class="data" v-if="info.name">
            <div class="label"><strong>Name:</strong> {{ info.name }}</div>
        </div>
        <div class="data" v-if="info.sbmlType">
            <div class="label"><strong>SBML Type:</strong> {{ info.sbmlType }}</div>
        </div>
        <div class="data" v-if="info.id">
            <div class="label"><strong>SID:</strong> {{ info.id }}</div>
        </div>
        <div class="data" v-if="info.sbo">
            <div class="label"><strong>SBO:</strong> {{ info.sbo }}</div>
        </div>
        <div class="data" v-if="info.metaId">
            <div class="label"><strong>Meta ID:</strong> {{ info.metaId }}</div>
        </div>
        <div class="data" v-if="info.history">
            <div class="label"><strong>History:</strong></div>
            <br />
            <div class="ml-4">
                <div class="label">Date Created: {{ info.history.createdDate }}</div>
                <br />
                <div class="label">Creators:</div>
                <ul title="Creators">
                    <li
                        v-for="creator in info.history.creators"
                        v-bind:key="creator.email"
                    >
                        {{ creator.givenName }} {{ creator.familyName }},
                        {{ creator.organization }} (<a
                            v-bind:href="`mailto:${creator.email}`"
                            >{{ creator.email }}</a
                        >)
                    </li>
                </ul>
                <div class="label">Dates Modified:</div>
                <ul title="Dates Modified">
                    <li v-for="date in info.history.modifiedDates" v-bind:key="date">
                        {{ date }}
                    </li>
                </ul>
            </div>
        </div>
        <div class="data" v-if="info.xml">
            <a-button type="info" @click="showModal">View XML</a-button>
        </div>
        <a-modal
            v-model:visible="visible"
            width="1000px"
            v-bind:title="`${info.name} - ${info.sbo}`"
            v-bind:footer="null"
            @ok="handleOk"
        >
            <p>{{ info.xml }}</p>
        </a-modal>

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
            infoData: {},
            visible: false,
        };
    },

    computed: {
        info: {
            set() {
                this.infoData = store.state.detailInfo;
            },
            get() {
                return store.state.detailInfo;
            },
        },
    },

    watch: {
        infoData: {
            handler (newValue) {
                console.log(newValue);
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
            },
            deep: true,
        },
        /*console.log(this.info.sbmlType);
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
        childContainer.child.appendChild(componentInstance.$el);*/
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
