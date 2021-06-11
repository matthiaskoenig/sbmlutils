<template>
    <!-- Name -->
    <div class="data" v-if="info.name">
        <div class="label"><strong>Name:</strong> {{ info.name }}</div>
    </div>

    <!-- SBML Type -->
    <div class="data" v-if="info.sbmlType">
        <div class="label"><strong>SBML Type:</strong> {{ info.sbmlType }}</div>
    </div>

    <!-- SID -->
    <div class="data" v-if="info.id">
        <div class="label"><strong>SID:</strong> {{ info.id }}</div>
    </div>

    <!-- SBO -->
    <div class="data" v-if="info.sbo">
        <div class="label"><strong>SBO:</strong> {{ info.sbo }}</div>
    </div>

    <!-- Meta ID -->
    <div class="data" v-if="info.metaId">
        <div class="label"><strong>Meta ID:</strong> {{ info.metaId }}</div>
    </div>

    <!-- History -->
    <div class="data" v-if="info.history">
        <div class="label"><strong>History:</strong></div>
        <br />
        <div class="ml-4">
            <div class="label">Date Created: {{ info.history.createdDate }}</div>
            <br />
            <div class="label">Creators:</div>
            <ul title="Creators">
                <li v-for="creator in info.history.creators" v-bind:key="creator.email">
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

    <!-- XML -->
    <button
        type="button"
        class="btn outline btn-info"
        data-toggle="modal"
        data-target="#exampleModalScrollable"
    >
        View XML
    </button>

    <!-- Modal -->
    <div
        class="modal fade"
        id="exampleModalScrollable"
        tabindex="-1"
        role="dialog"
        aria-labelledby="exampleModalScrollableTitle"
        aria-hidden="true"
    >
        <div class="modal-dialog modal-xl modal-dialog-scrollable" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <button
                        type="button"
                        class="close"
                        data-dismiss="modal"
                        aria-label="Close"
                    >
                        <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body">
                    <xml-container v-bind:xml="info.xml"></xml-container>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import store from "@/store/index";

import TYPES from "@/sbmlComponents";

/* Compartments */
import XMLContainer from "@/components/layout/XMLContainer.vue";

export default {
    props: {
        info: TYPES.SBase,
    },

    components: {
        "xml-container": XMLContainer,
    },

    data() {
        return {
            visible: false,
        };
    },

    methods: {
        showModal() {
            this.visible = true;
        },

        handleOk() {
            this.visible = false;
        },

        updateModalXML() {
            store.dispatch("updateXML", this.info.xml);
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/SBase.scss";
</style>
