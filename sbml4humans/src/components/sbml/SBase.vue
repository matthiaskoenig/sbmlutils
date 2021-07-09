<template>
    <!-- CORE -->
    <div class="d-flex justify-content-between">
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

    <!-- COMP -->
    <div class="data" v-if="info.replacedBy">
        <div class="label"><strong>replacedBy:</strong></div>
        <div class="ml-4">
            <div>submodelRef: {{ info.replacedBy.submodelRef }}</div>
            <div>
                replacedBySbaseref:
                {{ info.replacedBy.replacedBySbaseref.value }}
                (type: {{ info.replacedBy.replacedBySbaseref.type }})
            </div>
        </div>
    </div>
    <div class="data" v-if="info.replacedElements">
        <div class="label"><strong>replacedElements:</strong></div>
        <div class="ml-4">
            <ul title="Replaced Elements">
                <li
                    v-for="replacedElement in info.replacedElements"
                    v-bind:key="replacedElement.submodelRef"
                >
                    <div>
                        submodelRef:
                        <span
                            class="links"
                            v-on:click="
                                openComponent('Submodel:' + replacedElement.submodelRef)
                            "
                            >{{ replacedElement.submodelRef }}</span
                        >
                    </div>
                    <div>
                        replacedElementSbaseref:
                        {{ replacedElement.replacedElementSbaseref.value }}
                        (type: {{ replacedElement.replacedElementSbaseref.type }})
                    </div>
                </li>
            </ul>
        </div>
    </div>

    <!-- DISTRIB -->
    <div class="data" v-if="info.uncertainties">
        <div class="label"><strong>uncertainties:</strong></div>
        <div class="ml-4">
            <ol title="Uncertainties">
                <li v-for="uncertainty in info.uncertainties" v-bind:key="uncertainty">
                    Uncertainty Parameters
                    <ul title="Uncertainty Parameters">
                        <li
                            v-for="param in uncertainty.uncertaintyParameters"
                            v-bind:key="param"
                        >
                            <ul>
                                <li v-if="param.var">var: {{ param.var }}</li>
                                <li v-if="param.value">value: {{ param.value }}</li>
                                <li v-if="param.units">units: {{ param.units }}</li>
                                <li v-if="param.type">type: {{ param.type }}</li>
                                <li v-if="param.definitionURL">
                                    definitionURL: {{ param.definitionURL }}
                                </li>
                                <li v-if="param.math">math: {{ param.math }}</li>
                            </ul>
                        </li>
                    </ul>
                </li>
            </ol>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
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

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
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
