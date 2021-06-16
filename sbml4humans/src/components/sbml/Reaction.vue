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
    <div class="data" v-if="info.listOfReactants.length > 0">
        <div class="label"><strong>listOfReactants:</strong></div>
        <br />
        <div class="ml-4">
            <ul title="Reactants">
                <li
                    v-for="reactant in info.listOfReactants"
                    v-bind:key="reactant.species"
                >
                    {{ reactant.species }} [<span v-if="reactant.stoichiometry"
                        >stoichiometry: {{ reactant.stoichiometry }}</span
                    >
                    <span v-if="reactant.constant">, constant</span>]
                </li>
            </ul>
        </div>
    </div>

    <!-- List of Products -->
    <div class="data" v-if="info.listOfProducts.length > 0">
        <div class="label"><strong>listOfProducts:</strong></div>
        <br />
        <div class="ml-4">
            <ul title="Products">
                <li v-for="product in info.listOfProducts" v-bind:key="product.species">
                    {{ product.species }} [<span v-if="product.stoichiometry"
                        >stoichiometry: {{ product.stoichiometry }}</span
                    >
                    <span v-if="product.constant">, constant</span>]
                </li>
            </ul>
        </div>
    </div>

    <!-- List of Modifiers -->
    <div class="data" v-if="info.listOfModifiers.length > 0">
        <div class="label"><strong>listOfModifiers:</strong></div>
        <br />
        <div class="ml-4">
            <ul title="Modifiers">
                <li v-for="modifier in info.listOfModifiers" v-bind:key="modifier">
                    {{ modifier }}
                </li>
            </ul>
        </div>
    </div>

    <!-- Equation -->
    <div class="data" v-if="info.equation">
        <div class="label">
            <strong>equation:</strong>
            <span v-html="info.equation"></span>
        </div>
    </div>

    <!-- Fast -->
    <div class="data" v-if="info.fast">
        <div class="label"><strong>fast:</strong> {{ info.fast }}</div>
    </div>

    <!-- Kinetic Law (To be added after fixing the sbmlutils implementation)  -->

    <!-- FBC -->
    <div class="data" v-if="info.fbc">
        <div class="label"><strong>FBC:</strong> {{ info.fbc }}</div>
        <div class="ml-4">
            <div v-if="info.fbc.bounds">
                bounds: [<span v-if="info.fbc.bounds.lb_value">{{
                    info.fbc.bounds.lb_value
                }}</span
                >,
                <span v-if="info.fbc.bounds.ub_value">{{
                    info.fbc.bounds.ub_value
                }}</span
                >]
            </div>
            <div v-if="info.fbc.gpa">{{ info.fbc.gpa }}</div>
        </div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Reaction objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.Reaction,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
