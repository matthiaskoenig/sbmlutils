<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.compartment != null">
                <td class="label-td"><div class="label">compartment</div></td>
                <td>
                    <SBMLLink
                        :pk="'Compartment:' + info.compartment"
                        :sbmlType="String('Compartment')"
                    />
                </td>
            </tr>
            <tr v-if="info.initialAmount != null">
                <td><div class="label">initialAmount</div></td>
                <td>{{ info.initialAmount }}</td>
            </tr>
            <tr v-if="info.initialConcentration != null">
                <td class="label-td"><div class="label">initialConcentration</div></td>
                <td>{{ info.initialConcentration }}</td>
            </tr>
            <tr v-if="info.substanceUnits != null">
                <td class="label-td"><div class="label">substanceUnits</div></td>
                <td>{{ info.substanceUnits }}</td>
            </tr>
            <tr v-if="info.hasOnlySubstanceUnits != null">
                <td class="label-td">
                    <div class="label">hasOnlySubstanceUnits</div>
                </td>
                <td>
                    <boolean-symbol
                        v-if="info.hasOnlySubstanceUnits === Boolean(true)"
                        :value="info.hasOnlySubstanceUnits"
                    />
                    <boolean-symbol v-else :value="Boolean(false)" />
                </td>
            </tr>
            <tr v-if="info.boundaryCondition != null">
                <td class="label-td"><div class="label">boundaryCondition</div></td>
                <td>
                    <boolean-symbol
                        v-if="info.boundaryCondition === Boolean(true)"
                        :value="info.boundaryCondition"
                    />
                    <boolean-symbol v-else :value="Boolean(false)" />
                </td>
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
            <tr v-if="info.conversionFactor != null && info.conversionFactor.sid">
                <td class="label-td"><div class="label">conversionFactor</div></td>
                <td>
                    {{ info.conversionFactor.sid }} = {{ info.conversionFactor.value }}
                    {{ info.conversionFactor.units }}
                </td>
            </tr>
            <tr v-if="info.fbc && (info.fbc.formula || info.fbc.charge)">
                <td class="label-td"><div class="label">fbc</div></td>
                <td>
                    <span v-if="info.fbc.formula">formula: {{ info.fbc.formula }}</span
                    ><br />
                    <span v-if="info.fbc.charge">charge: {{ info.fbc.charge }}</span>
                </td>
            </tr>
            <tr v-if="info.reactant && info.reactant.length">
                <td class="label-td"><div class="label">reactant</div></td>
                <td>
                    <SBMLLink
                        v-for="reactant in info.reactant"
                        :key="reactant"
                        :pk="reactant"
                        :sbmlType="String('Reaction')"
                    />
                </td>
            </tr>
            <tr v-if="info.product && info.product.length">
                <td class="label-td"><div class="label">product</div></td>
                <td>
                    <SBMLLink
                        v-for="product in info.product"
                        :key="product"
                        :pk="product"
                        :sbmlType="String('Reaction')"
                    />
                </td>
            </tr>
            <tr v-if="info.modifier && info.modifier.length">
                <td class="label-td"><div class="label">modifier</div></td>
                <td>
                    <SBMLLink
                        v-for="modifier in info.modifier"
                        :key="modifier"
                        :pk="modifier"
                        :sbmlType="String('Reaction')"
                    />
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import SBMLLink from "@/components/layout/SBMLLink.vue";
import Katex from "@/components/layout/Katex.vue";
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

/**
 * Component to define display of Species objects.
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
            default: TYPES.Species,
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
