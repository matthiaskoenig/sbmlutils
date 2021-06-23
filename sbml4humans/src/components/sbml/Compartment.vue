<template>
    <!-- Spatial Dimensions -->
    <div class="data" v-if="info.spatialDimensions">
        <div class="label">
            <strong>spatialDimensions:</strong> {{ info.spatialDimensions }}
        </div>
    </div>

    <!-- Size -->
    <div class="data" v-if="info.size">
        <div class="label"><strong>size:</strong> {{ info.size }}</div>
    </div>

    <!-- Constant -->
    <div class="data" v-if="info.constant">
        <div class="label"><strong>constant:</strong> {{ info.constant }}</div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units">
        <div class="label">
            <strong>units:</strong>
            <katex v-bind:mathStr="info.units"></katex>
        </div>
    </div>

    <!-- Derived Units -->
    <div class="data" v-if="info.derivedUnits">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex v-bind:mathStr="info.derivedUnits"></katex>
        </div>
    </div>

    <!-- Assignment -->
    <div class="data" v-if="info.assignment">
        <div class="label">
            <strong>assignment:</strong>
            <span>{{ info.assignment.pk }} ({{ info.assignment.sbmlType }})</span>
        </div>
    </div>

    <!-- List of Related Species -->
    <div class="data" v-if="info.species">
        <div class="label">
            <strong>relatedSpecies:</strong>
        </div>
        <div class="ml-4">
            <ul title="List of Related Species">
                <li v-for="species in info.species" v-bind:key="species">
                    {{ species }}
                </li>
            </ul>
        </div>
    </div>

    <!-- List of Related Reactions -->
    <div class="data" v-if="info.reaction">
        <div class="label">
            <strong>relatedReactions:</strong>
        </div>
        <div class="ml-4">
            <ul title="List of Related Reactions">
                <li v-for="reaction in info.reactions" v-bind:key="reaction">
                    {{ reaction }}
                </li>
            </ul>
        </div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of Compartment objects.
 */
export default defineComponent({
    components: {
        katex: Katex,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Compartment,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
