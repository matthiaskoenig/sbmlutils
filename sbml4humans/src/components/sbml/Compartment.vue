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
        <div class="label">
            <strong>constant:</strong
            ><boolean-symbol :value="info.constant"></boolean-symbol>
        </div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units">
        <div class="label">
            <strong>units:</strong>
            <katex :mathStr="info.units"></katex>
        </div>
    </div>

    <!-- Derived Units -->
    <div class="data" v-if="info.derivedUnits">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex :mathStr="info.derivedUnits"></katex>
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
    <div class="data w-100" v-if="info.species">
        <div class="label">
            <strong>relatedSpecies:</strong>
        </div>
        <div class="ml-4 tag-list">
            <div v-for="species in info.species" :key="species">
                <SBMLLink :pk="species" :sbmlType="String('Species')"></SBMLLink>
            </div>
        </div>
    </div>

    <!-- List of Related Reactions -->
    <div class="data w-100" v-if="info.reaction">
        <div class="label">
            <strong>relatedReactions:</strong>
        </div>
        <div class="ml-4 tag-list">
            <div v-for="reaction in info.reaction" :key="reaction">
                <SBMLLink :pk="reaction" :sbmlType="String('Reaction')"></SBMLLink>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";
import SBMLLink from "@/components/layout/SBMLLink.vue";
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

/**
 * Component to define display of Compartment objects.
 */
export default defineComponent({
    components: {
        katex: Katex,
        SBMLLink: SBMLLink,
        "boolean-symbol": BooleanSymbol,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Compartment,
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
@import "@/assets/styles/scss/SBase.scss";

.tag-list {
    width: auto;
    display: flex;
    flex-wrap: wrap;
}
</style>
