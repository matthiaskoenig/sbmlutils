<template>
    <!-- Spatial Dimensions -->
    <div class="data" v-if="info.spatialDimensions != null">
        <div class="label">
            <strong>spatialDimensions:</strong> {{ info.spatialDimensions }}
        </div>
    </div>

    <!-- Size -->
    <div class="data" v-if="info.size != null">
        <div class="label"><strong>size:</strong> {{ info.size }}</div>
    </div>

    <!-- Constant -->
    <div class="data" v-if="info.constant != null">
        <div class="label">
            <strong>constant:</strong
            ><boolean-symbol
                v-if="info.constant === Boolean(true)"
                :value="info.constant"
            />
            <boolean-symbol v-else :value="Boolean(false)" />
        </div>
    </div>

    <!-- Units -->
    <div class="data" v-if="info.units != null">
        <div class="label">
            <strong>units:</strong>
            <katex :mathStr="info.units" />
        </div>
    </div>

    <!-- Derived Units -->
    <div class="data" v-if="info.derivedUnits != null">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex :mathStr="info.derivedUnits" />
        </div>
    </div>

    <!-- Assignment -->
    <div class="data" v-if="info.assignment != null">
        <div class="label">
            <strong>assignment:</strong>
            <span>{{ info.assignment.pk }} ({{ info.assignment.sbmlType }})</span>
        </div>
    </div>

    <!-- List of Related Species -->
    <div class="data w-100" v-if="info.species != null">
        <div class="label">
            <strong>relatedSpecies:</strong>
        </div>
        <div class="ml-4 tag-list">
            <div v-for="species in info.species" :key="species">
                <SBMLLink :pk="species" :sbmlType="String('Species')" />
            </div>
        </div>
    </div>

    <!-- List of Related Reactions -->
    <div class="data w-100" v-if="info.reaction != null">
        <div class="label">
            <strong>relatedReactions:</strong>
        </div>
        <div class="ml-4 tag-list">
            <div v-for="reaction in info.reaction" :key="reaction">
                <SBMLLink :pk="reaction" :sbmlType="String('Reaction')" />
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
        Katex,
        SBMLLink,
        BooleanSymbol,
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
</style>
