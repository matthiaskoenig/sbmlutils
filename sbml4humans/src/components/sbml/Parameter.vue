<template>
    <!-- Value -->
    <div class="data" v-if="info.value != null">
        <div class="label"><strong>value:</strong> {{ info.value }}</div>
    </div>

    <!-- Constant -->
    <div class="data" v-if="info.constant != null">
        <div class="label">
            <strong>constant:</strong>
            <boolean-symbol
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
            <Katex :mathStr="info.units" />
        </div>
    </div>

    <!-- Derived Units -->
    <div class="data" v-if="info.derivedUnits != null">
        <div class="label">
            <strong>derivedUnits:</strong>
            <Katex :mathStr="info.derivedUnits" />
        </div>
    </div>

    <!-- Assignment -->
    <div class="data" v-if="info.assignment != null">
        <div class="label">
            <strong>assignment:</strong>
            <span>{{ info.assignment.pk }} ({{ info.assignment.sbmlType }})</span>
        </div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

/**
 * Component to define display of Parameter objects.
 */
export default defineComponent({
    components: {
        Katex,
        BooleanSymbol,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Parameter,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
