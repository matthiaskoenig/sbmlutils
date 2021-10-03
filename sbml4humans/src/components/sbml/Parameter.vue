<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.value != null">
                <td><div class="label">value</div></td>
                <td>{{ info.value }}</td>
            </tr>
            <tr v-if="info.constant != null">
                <td class="label-td"><div class="label">constant</div></td>
                <td>
                    <boolean-symbol
                        v-if="info.constant === Boolean(true)"
                        :value="info.constant"
                    />
                    <boolean-symbol v-else :value="Boolean(false)" />
                </td>
            </tr>
            <tr v-if="info.units != null">
                <td class="label-td"><div class="label">units</div></td>
                <td><katex :mathStr="info.units" class="katex_unit" /></td>
            </tr>
            <tr v-if="info.derivedUnits != null">
                <td class="label-td"><div class="label">derivedUnits</div></td>
                <td><katex :mathStr="info.derivedUnits" class="katex_unit" /></td>
            </tr>
            <tr v-if="info.assignment != null">
                <td class="label-td"><div class="label">assignment</div></td>
                <td>
                    <katex :mathStr="info.assignment.math" />
                </td>
            </tr>
            <tr v-if="info.port != null">
                <td class="label-td"><div class="label">port</div></td>
                <td>
                    <SBMLLink
                        :pk="info.port.pk"
                        :sbmlType="String(info.port.sbmlType)"
                    />
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";
import SBMLLink from "@/components/layout/SBMLLink.vue";

/**
 * Component to define display of Parameter objects.
 */
export default defineComponent({
    components: {
        Katex,
        BooleanSymbol,
        // SBMLLink,
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
