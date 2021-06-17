<template>
    <!-- Name -->
    <div class="data" v-if="info.name">
        <div class="label"><strong>name:</strong> {{ info.name }}</div>
    </div>

    <!-- SBML Type -->
    <div class="data" v-if="info.sbmlType">
        <div class="label"><strong>sbmlType:</strong> {{ info.sbmlType }}</div>
    </div>

    <!-- SID -->
    <div class="data" v-if="info.id">
        <div class="label"><strong>id:</strong> {{ info.id }}</div>
    </div>

    <!-- SBO -->
    <div class="data" v-if="info.sbo">
        <div class="label"><strong>sbo:</strong> {{ info.sbo }}</div>
    </div>

    <!-- Meta ID -->
    <div class="data" v-if="info.metaId">
        <div class="label"><strong>metaId:</strong> {{ info.metaId }}</div>
    </div>

    <!-- History -->
    <div class="data" v-if="info.history">
        <div class="label"><strong>history:</strong></div>
        <br />
        <div class="ml-4">
            <div class="label">createdDate: {{ info.history.createdDate }}</div>
            <br />
            <div class="label">creators:</div>
            <ul title="Creators">
                <li v-for="creator in info.history.creators" v-bind:key="creator.email">
                    {{ creator.givenName }} {{ creator.familyName }},
                    {{ creator.organization }} (<a
                        v-bind:href="`mailto:${creator.email}`"
                        >{{ creator.email }}</a
                    >)
                </li>
            </ul>
            <div class="label">modifiedDates:</div>
            <ul title="Dates Modified">
                <li v-for="date in info.history.modifiedDates" v-bind:key="date">
                    {{ date }}
                </li>
            </ul>
        </div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of SBase information.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.SBase,
        },
        math: {
            type: String,
            default: "",
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/SBase.scss";
</style>
