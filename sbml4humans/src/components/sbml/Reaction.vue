<template>
    <!-- Reversible -->
    <div class="data" v-if="info.reversible">
        <div class="label"><strong>reversible:</strong> {{ info.reversible }}</div>
    </div>

    <!-- Compartment -->
    <div class="data" v-if="info.compartment">
        <div class="label"><strong>compartment:</strong> {{ info.compartment }}</div>
    </div>

    <!-- List of Reactants -->
    <div class="data" v-if="info.listOfReactants && info.listOfReactants.length > 0">
        <div class="label"><strong>listOfReactants:</strong></div>
        <br />
        <div class="ml-4">
            <ul title="Reactants">
                <li
                    v-for="reactant in info.listOfReactants"
                    v-bind:key="reactant.species"
                >
                    <span class="links" v-on:click="openComponent('Species:' + reactant.species)">{{
                        reactant.species
                    }}</span>
                    [<span v-if="reactant.stoichiometry"
                        >stoichiometry: {{ reactant.stoichiometry }}</span
                    >
                    <span v-if="reactant.constant">, constant</span>]
                </li>
            </ul>
        </div>
    </div>

    <!-- List of Products -->
    <div class="data" v-if="info.listOfProducts && info.listOfProducts.length > 0">
        <div class="label"><strong>listOfProducts:</strong></div>
        <br />
        <div class="ml-4">
            <ul title="Products">
                <li v-for="product in info.listOfProducts" v-bind:key="product.species">
                    <span class="links" v-on:click="openComponent('Species:' + product.species)">{{
                        product.species
                    }}</span>
                    [<span v-if="product.stoichiometry"
                        >stoichiometry: {{ product.stoichiometry }}</span
                    >
                    <span v-if="product.constant">, constant</span>]
                </li>
            </ul>
        </div>
    </div>

    <!-- List of Modifiers -->
    <div class="data" v-if="info.listOfModifiers && info.listOfModifiers.length > 0">
        <div class="label"><strong>listOfModifiers:</strong></div>
        <br />
        <div class="ml-4">
            <ul title="Modifiers">
                <li v-for="modifier in info.listOfModifiers" v-bind:key="modifier">
                    <span class="links" v-on:click="openComponent('Species:' + modifier)">{{
                        modifier
                    }}</span>
                </li>
            </ul>
        </div>
    </div>

    <!-- Equation -->
    <div class="data" v-if="info.equation">
        <div class="label">
            <strong>equation:</strong>
            <span class="ml-2" v-html="info.equation"></span>
        </div>
    </div>

    <!-- Fast -->
    <div class="data" v-if="info.fast">
        <div class="label"><strong>fast:</strong> {{ info.fast }}</div>
    </div>

    <!-- Kinetic Law -->
    <div class="data" v-if="info.kineticLaw">
        <div class="label">
            <strong>kineticLaw:</strong>
        </div>
        <div class="ml-4">
            <div v-if="info.kineticLaw.math">
                math: <Katex v-bind:mathStr="info.kineticLaw.math" />
            </div>
            <div v-if="info.kineticLaw.derivedUnits">
                derivedUnits: <Katex v-bind:mathStr="info.kineticLaw.derivedUnits" />
            </div>
            <div v-if="info.kineticLaw.listOfLocalParameters">
                listOfLocalParameters:
                <ul title="listOfLocalParameters">
                    <li
                        v-for="lpar in info.kineticLaw.listOfLocalParameters"
                        v-bind:key="lpar.id"
                    >
                        <div v-if="lpar.id">id: {{ lpar.id }}</div>
                        <div v-if="lpar.value">value: {{ lpar.value }}</div>
                        <div v-if="lpar.units">
                            units: <katex v-bind:mathStr="lpar.units"></katex>
                        </div>
                        <div v-if="lpar.derivedUnits">
                            derivedUnits:
                            <katex v-bind:mathStr="lpar.derivedUnits"></katex>
                        </div>
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <!-- FBC -->
    <div class="data" v-if="info.fbc">
        <div class="label"><strong>FBC:</strong> {{ info.fbc }}</div>
        <div class="ml-4">
            <div v-if="info.fbc.bounds">
                <div v-if="info.fbc.bounds.lowerFluxBound">
                    lowerFluxBound:
                    <span>
                        id: {{ info.fbc.bounds.lowerFluxBound.id }}, value:
                        {{ info.fbc.bounds.lowerFluxBound.value }}</span
                    >
                </div>
                <div v-if="info.fbc.bounds.upperFluxBound">
                    upperFluxBound:
                    <span>
                        id: {{ info.fbc.bounds.upperFluxBound.id }}, value:
                        {{ info.fbc.bounds.upperFluxBound.value }}</span
                    >
                </div>
            </div>
            <div v-if="info.fbc.gpa">{{ info.fbc.gpa }}</div>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of Reaction objects.
 */
export default defineComponent({
    components: {
        Katex,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Reaction,
        },
    },

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
