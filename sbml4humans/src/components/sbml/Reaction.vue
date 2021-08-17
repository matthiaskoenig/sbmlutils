<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
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
            <tr v-if="info.equation != null">
                <td class="label-td"><div class="label">equation</div></td>
                <td><span class="p-ml-2" v-html="info.equation"></span></td>
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
                    <div v-if="info.kineticLaw.derivedUnits != null">
                        derivedUnits: <Katex :mathStr="info.kineticLaw.derivedUnits" />
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
            <tr v-if="info.fbc != null">
                <td class="label-td"><div class="label">fbc</div></td>
                <td>
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
            <tr v-if="info.listOfReactants != null && info.listOfReactants.length > 0">
                <td class="label-td"><div class="label">reactants</div></td>
                <td>
                    <div
                        v-for="reactant in info.listOfReactants"
                        :key="reactant.species"
                    >
                        <SBMLLink
                            :pk="'Species:' + reactant.species"
                            :sbmlType="String('Species')"
                        />
                        [<span v-if="reactant.stoichiometry != null"
                            >stoichiometry: {{ reactant.stoichiometry }}</span
                        >
                        <span v-if="reactant.constant != null">, constant</span>]
                    </div>
                </td>
            </tr>
            <tr v-if="info.listOfProducts != null && info.listOfProducts.length > 0">
                <td class="label-td"><div class="label">products</div></td>
                <td>
                    <div v-for="product in info.listOfProducts" :key="product.species">
                        <SBMLLink
                            :pk="'Species:' + product.species"
                            :sbmlType="String('Species')"
                        />
                        [<span v-if="product.stoichiometry != null"
                            >stoichiometry: {{ product.stoichiometry }}</span
                        >
                        <span v-if="product.constant != null">, constant</span>]
                    </div>
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

    <!-- <div class="data" v-if="info.reversible != null">
        <div class="label">
            <strong>reversible:</strong>
            <boolean-symbol
                v-if="info.reversible === Boolean(true)"
                :value="info.reversible"
            />
            <boolean-symbol v-else :value="Boolean(false)" />
        </div>
    </div>

    <div class="data" v-if="info.compartment != null">
        <div class="label"><strong>compartment:</strong> {{ info.compartment }}</div>
    </div>

    <div
        class="data"
        v-if="info.listOfReactants != null && info.listOfReactants.length > 0"
    >
        <div class="label"><strong>listOfReactants:</strong></div>
        <br />
        <div class="p-ml-4">
            <div v-for="reactant in info.listOfReactants" :key="reactant.species">
                <SBMLLink
                    :pk="'Species:' + reactant.species"
                    :sbmlType="String('Species')"
                />
                [<span v-if="reactant.stoichiometry != null"
                    >stoichiometry: {{ reactant.stoichiometry }}</span
                >
                <span v-if="reactant.constant != null">, constant</span>]
            </div>
        </div>
    </div>

    <div
        class="data"
        v-if="info.listOfProducts != null && info.listOfProducts.length > 0"
    >
        <div class="label"><strong>listOfProducts:</strong></div>
        <br />
        <div class="p-ml-4">
            <div v-for="product in info.listOfProducts" :key="product.species">
                <SBMLLink
                    :pk="'Species:' + product.species"
                    :sbmlType="String('Species')"
                />
                [<span v-if="product.stoichiometry != null"
                    >stoichiometry: {{ product.stoichiometry }}</span
                >
                <span v-if="product.constant != null">, constant</span>]
            </div>
        </div>
    </div>

    <div
        class="data"
        v-if="info.listOfModifiers != null && info.listOfModifiers.length > 0"
    >
        <div class="label"><strong>listOfModifiers:</strong></div>
        <br />
        <div class="p-ml-4">
            <div
                class="p-d-flex"
                v-for="modifier in info.listOfModifiers"
                :key="modifier"
            >
                <SBMLLink :pk="'Species:' + modifier" :sbmlType="String('Species')" />
            </div>
        </div>
    </div>

    <div class="data" v-if="info.equation != null">
        <div class="label">
            <strong>equation:</strong>
            <span class="p-ml-2" v-html="info.equation"></span>
        </div>
    </div>

    <div class="data" v-if="info.fast != null">
        <div class="label">
            <strong>fast:</strong>
            <boolean-symbol v-if="info.fast === Boolean(true)" :value="info.fast" />
            <boolean-symbol v-else :value="Boolean(false)" />
        </div>
    </div>

    <div class="data" v-if="info.kineticLaw != null">
        <div class="label">
            <strong>kineticLaw:</strong>
        </div>
        <div class="p-ml-4">
            <div v-if="info.kineticLaw.math != null">
                math: <Katex :mathStr="info.kineticLaw.math" />
            </div>
            <div v-if="info.kineticLaw.derivedUnits != null">
                derivedUnits: <Katex :mathStr="info.kineticLaw.derivedUnits" />
            </div>
            <div v-if="info.kineticLaw.listOfLocalParameters != null">
                listOfLocalParameters:
                <ul title="listOfLocalParameters">
                    <li
                        v-for="lpar in info.kineticLaw.listOfLocalParameters"
                        :key="lpar.id"
                    >
                        <div v-if="lpar.id != null">id: {{ lpar.id }}</div>
                        <div v-if="lpar.value != null">value: {{ lpar.value }}</div>
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
        </div>
    </div>

    <div class="data" v-if="info.fbc">
        <div class="label"><strong>FBC:</strong></div>
        <div class="p-ml-4">
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
    </div> -->
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
