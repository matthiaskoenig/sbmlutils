<template>
    <div class="d-flex justify-content-between w-100">
        <h1 class="sbmlType px-2 py-1" v-bind:style="`background-color: ${color}`">
            {{ info.sbmlType }}
        </h1>
        <detail-view-nav></detail-view-nav>
    </div>
    <h2>{{ info.id }} {{ info.name ? "(" + info.name + ")" : "" }}</h2>

    <div class="data" v-if="info.id">
        <div class="label"><strong>id:</strong> {{ info.id }}</div>
    </div>
    <div class="data" v-if="info.metaId">
        <div class="label"><strong>metaId:</strong> {{ info.metaId }}</div>
    </div>
    <div class="data" v-if="info.name">
        <div class="label"><strong>name:</strong> {{ info.name }}</div>
    </div>
    <div class="data" v-if="info.sbo">
        <div class="label"><strong>sbo:</strong> {{ info.sbo }}</div>
    </div>
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
    <div class="data" v-if="info.cvterms">
        <div class="label"><strong>cvterms:</strong></div>
        <div class="ml-4">
            <ul title="CVTerms">
                <li v-for="cvterm in info.cvterms" v-bind:key="cvterm.qualifier">
                    <div>qualifier: {{ cvterm.qualifier }}</div>
                    <div>resources:</div>
                    <ul class="ml-4">
                        <li v-for="resource in cvterm.resources" v-bind:key="resource">
                            {{ resource }}
                        </li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>
</template>

<script lang="ts">
import colorScheme from "@/data/colorScheme";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import DetailViewNav from "@/components/layout/DetailViewNav.vue";

/**
 * Component to define display of SBase information.
 */
export default defineComponent({
    components: {
        "detail-view-nav": DetailViewNav,
    },

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

    computed: {
        color(): string {
            return colorScheme.componentColor[this.info.sbmlType];
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/SBase.scss";
</style>
