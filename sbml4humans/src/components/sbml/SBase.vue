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
    <div class="data" v-if="info.xml">
        <a-button type="info" @click="showModal">View XML</a-button>
    </div>
    <a-modal
        v-model:visible="visible"
        width="1000px"
        v-bind:footer="null"
        @ok="handleOk"
    >
        <p>{{ info.xml }}</p>
    </a-modal>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        //FIXME: initialize with empty data
        info: TYPES.SBase,
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
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/SBase.scss";
</style>
