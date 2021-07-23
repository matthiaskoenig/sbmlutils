<template>
    <!-- CORE -->
    <div class="d-flex justify-content-between">
        <strong class="sbmlType" :style="`background-color: ${color}`">
            <i :class="`fas fa-${icon} mr-2`"></i>{{ info.sbmlType }}
        </strong>
        <detail-view-nav></detail-view-nav>
    </div>
    <h2>{{ info.id }} {{ info.name ? "(" + info.name + ")" : "" }}</h2>

    <div class="data" v-if="info.id != null">
        <div class="label"><strong>id:</strong> {{ info.id }}</div>
    </div>
    <div class="data" v-if="info.metaId != null">
        <div class="label"><strong>metaId:</strong> {{ info.metaId }}</div>
    </div>
    <div class="data" v-if="info.name != null">
        <div class="label"><strong>name:</strong> {{ info.name }}</div>
    </div>
    <div class="data" v-if="info.sbo != null">
        <div class="label"><strong>sbo:</strong> {{ info.sbo }}</div>
    </div>
    <div class="data" v-if="info.history != null">
        <div class="label"><strong>history:</strong></div>
        <br />
        <div class="ml-4">
            <div class="label">createdDate: {{ info.history.createdDate }}</div>
            <br />
            <div class="label">creators:</div>
            <ul title="Creators">
                <li v-for="creator in info.history.creators" :key="creator.email">
                    {{ creator.givenName }} {{ creator.familyName }},
                    {{ creator.organization }} (<a :href="`mailto:${creator.email}`">{{
                        creator.email
                    }}</a
                    >)
                </li>
            </ul>
            <div class="label">modifiedDates:</div>
            <ul title="Dates Modified">
                <li v-for="date in info.history.modifiedDates" :key="date">
                    {{ date }}
                </li>
            </ul>
        </div>
    </div>

    <div class="data" v-if="info.cvterms != null">
        <div class="label"><strong>cvterms:</strong></div>
        <div class="ml-4">
            <ul title="CVTerms">
                <li v-for="cvterm in info.cvterms" :key="cvterm.qualifier">
                    <div>qualifier: {{ cvterm.qualifier }}</div>
                    <div>resources:</div>
                    <ul class="ml-4">
                        <li v-for="resource in cvterm.resources" :key="resource">
                            <a :href="resource" target="_blank">{{ resource }}</a>
                        </li>
                    </ul>
                </li>
            </ul>
        </div>
    </div>

    <!-- COMP -->
    <div class="data" v-if="info.replacedBy != null">
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
    <div class="data" v-if="info.replacedElements != null">
        <div class="label"><strong>replacedElements:</strong></div>
        <div class="ml-4">
            <ul title="Replaced Elements">
                <li
                    v-for="replacedElement in info.replacedElements"
                    :key="replacedElement.submodelRef"
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
                <li v-for="uncertainty in info.uncertainties" :key="uncertainty">
                    Uncertainty Parameters
                    <ul title="Uncertainty Parameters">
                        <li
                            v-for="param in uncertainty.uncertaintyParameters"
                            :key="param"
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
import icons from "@/data/fontAwesome";
import colorScheme from "@/data/colorScheme";
import TYPES from "@/data/sbmlComponents";
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

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },

    computed: {
        color(): string {
            return colorScheme.componentColor[this.info.sbmlType];
        },

        icon(): string {
            return icons.icons[this.info.sbmlType];
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
