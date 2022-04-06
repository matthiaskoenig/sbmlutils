<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.equation != null">
                <td class="label-td"><div class="label">equation</div></td>
                <td><span class="p-ml-2" v-html="info.equation"></span></td>
            </tr>
            <tr v-if="info.reversible != null">
                <td class="label-td"><div class="label">reversible</div></td>
                <td>
                    <boolean-symbol
                        v-if="info.reversible === Boolean(true)"
                        :value="info.reversible"
                    />
                    <boolean-symbol v-else :value="Boolean(false)" />
                </td>
            </tr>
            <tr v-if="info.fast != null">
                <td class="label-td"><div class="label">fast</div></td>
                <td>
                    <boolean-symbol
                        v-if="info.fast === Boolean(true)"
                        :value="info.fast"
                    />
                    <boolean-symbol v-else :value="Boolean(false)" />
                </td>
            </tr>
            <tr v-if="info.kineticLaw != null">
                <td class="label-td"><div class="label">kineticLaw</div></td>
                <td>
                    <div v-if="info.kineticLaw.math != null">
                        <Katex :mathStr="info.kineticLaw.math" />
                    </div>
                    <div v-if="info.kineticLaw.listOfLocalParameters != null">
                        listOfLocalParameters:
                        <ul title="listOfLocalParameters">
                            <li
                                v-for="lpar in info.kineticLaw.listOfLocalParameters"
                                :key="lpar.id"
                            >
                                <div v-if="lpar.id != null">id: {{ lpar.id }}</div>
                                <div v-if="lpar.value != null">
                                    value: {{ lpar.value }}
                                </div>
                                <div v-if="lpar.units != null">
                                    units: <katex :mathStr="lpar.units" />
                                </div>
                                <div v-if="lpar.derivedUnits != null">
                                    derivedUnits:
                                    <katex :mathStr="lpar.derivedUnits" />
                                </div>
                            </li>
                        </ul>
                    </div>
                </td>
            </tr>
            <tr v-if="info.kineticLaw != null">
                <td class="label-td"><div class="label">derivedUnits</div></td>
                <td>
                    <div v-if="info.kineticLaw.derivedUnits != null">
                        <katex
                            :mathStr="info.kineticLaw.derivedUnits"
                            class="katex_unit"
                        />
                    </div>
                </td>
            </tr>

            <tr v-if="info.fbc != null">
                <td class="label-td"><div class="label">gpa</div></td>
                <td>
                    <div v-if="info.fbc.gpa">{{ info.fbc.gpa }}</div>
                </td>
            </tr>
            <tr v-if="info.fbc != null">
                <td class="label-td"><div class="label">lowerFluxBound</div></td>
                <td>
                    <div
                        v-if="
                            info.fbc.bounds &&
                            info.fbc.bounds.lowerFluxBound &&
                            info.fbc.bounds.lowerFluxBound.id
                        "
                    >
                        {{ info.fbc.bounds.lowerFluxBound.id }} =
                        {{ info.fbc.bounds.lowerFluxBound.value }}
                    </div>
                </td>
            </tr>
            <tr v-if="info.fbc != null">
                <td class="label-td"><div class="label">upperFluxBound</div></td>
                <td>
                    <div
                        v-if="
                            info.fbc.bounds &&
                            info.fbc.bounds.upperFluxBound &&
                            info.fbc.bounds.upperFluxBound.id
                        "
                    >
                        {{ info.fbc.bounds.upperFluxBound.id }} =
                        {{ info.fbc.bounds.upperFluxBound.value }}
                    </div>
                </td>
            </tr>

            <tr v-if="info.compartment != null">
                <td class="label-td"><div class="label">compartment</div></td>
                <td>
                    <SBMLLink
                        :pk="'Compartment:' + info.compartment"
                        :sbmlType="String('Compartment')"
                    />
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
            <tr v-if="info.listOfReactants != null && info.listOfReactants.length > 0">
                <td class="label-td"><div class="label">reactants</div></td>
                <td>
                    <span
                        v-for="reactant in info.listOfReactants"
                        :key="reactant.species"
                    >
                        <SBMLLink
                            :pk="'Species:' + reactant.species"
                            :sbmlType="String('Species')"
                        />
                    </span>
                </td>
            </tr>
            <tr v-if="info.listOfProducts != null && info.listOfProducts.length > 0">
                <td class="label-td"><div class="label">products</div></td>
                <td>
                    <span v-for="product in info.listOfProducts" :key="product.species">
                        <SBMLLink
                            :pk="'Species:' + product.species"
                            :sbmlType="String('Species')"
                        />
                    </span>
                </td>
            </tr>
            <tr v-if="info.listOfModifiers != null && info.listOfModifiers.length > 0">
                <td class="label-td"><div class="label">modifiers</div></td>
                <td>
                    <div
                        class="p-d-flex"
                        v-for="modifier in info.listOfModifiers"
                        :key="modifier"
                    >
                        <SBMLLink
                            :pk="'Species:' + modifier"
                            :sbmlType="String('Species')"
                        />
                    </div>
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script lang="ts">
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";
import SBMLLink from "@/components/layout/SBMLLink.vue";
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

/**
 * Component to define display of Reaction objects.
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
@import "@/assets/styles/scss/SBase.scss";
</style>
