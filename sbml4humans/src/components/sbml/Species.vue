<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
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
                <td><Katex :mathStr="info.units" /></td>
            </tr>
            <tr v-if="info.derivedUnits != null">
                <td class="label-td"><div class="label">derivedUnits</div></td>
                <td><Katex :mathStr="info.derivedUnits" /></td>
            </tr>
            <tr v-if="info.assignment != null">
                <td class="label-td"><div class="label">assignment</div></td>
                <td>
                    <span
                        >{{ info.assignment.pk }} ({{ info.assignment.sbmlType }})</span
                    >
                </td>
            </tr>
            <tr
                v-if="
                    info.conversionFactor != null &&
                    (info.conversionFactor.sid ||
                        info.conversionFactor.value ||
                        info.conversionFactor.units)
                "
            >
                <td class="label-td"><div class="label">conversionFactor</div></td>
                <td>
                    <ul title="Conversion Factor">
                        <li v-if="info.conversionFactor.sid">
                            sid: {{ info.conversionFactor.sid }}
                        </li>
                        <li v-if="info.conversionFactor.value">
                            value: {{ info.conversionFactor.value }}
                        </li>
                        <li v-if="info.conversionFactor.units">
                            units: {{ info.conversionFactor.units }}
                        </li>
                    </ul>
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
            <tr v-if="info.compartment != null">
                <td class="label-td"><div class="label">compartment</div></td>
                <td>
                    <SBMLLink
                        :pk="'Compartment:' + info.compartment"
                        :sbmlType="String('Compartment')"
                    />
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

    <!-- Compartment
    <div class="data" v-if="info.compartment != null">
        <div class="label"><strong>compartment: </strong></div>
        <div class="p-ml-3">
            <SBMLLink
                :pk="'Compartment:' + info.compartment"
                :sbmlType="String('Compartment')"
            />
        </div>
    </div>

    <div class="data" v-if="info.initialAmount != null">
        <div class="label">
            <strong>initialAmount:</strong> {{ info.initialAmount }}
        </div>
    </div>

    <div class="data" v-if="info.initialConcentration != null">
        <div class="label">
            <strong>initialConcentration:</strong> {{ info.initialConcentration }}
        </div>
    </div>

    <div class="data" v-if="info.substanceUnits != null">
        <div class="label">
            <strong>substanceUnits:</strong> {{ info.substanceUnits }}
        </div>
    </div>

    <div class="data" v-if="info.hasOnlySubstanceUnits != null">
        <div class="label">
            <strong>hasOnlySubstanceUnits:</strong>
            <boolean-symbol
                v-if="info.hasOnlySubstanceUnits === Boolean(true)"
                :value="info.hasOnlySubstanceUnits"
            />
            <boolean-symbol v-else :value="Boolean(false)" />
        </div>
    </div>

    <div class="data" v-if="info.boundaryCondition != null">
        <div class="label">
            <strong>boundaryCondition:</strong>
            <boolean-symbol
                v-if="info.boundaryCondition === Boolean(true)"
                :value="info.boundaryCondition"
            />
            <boolean-symbol v-else :value="Boolean(false)" />
        </div>
    </div>

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

    <div class="data" v-if="info.units != null">
        <div class="label">
            <strong>units:</strong>
            <Katex :mathStr="info.units" />
        </div>
    </div>

    <div class="data" v-if="info.derivedUnits != null">
        <div class="label">
            <strong>derivedUnits:</strong>
            <Katex :mathStr="info.derivedUnits" />
        </div>
    </div>

    <div class="data" v-if="info.assignment != null">
        <div class="label">
            <strong>assignment:</strong>
            <span>{{ info.assignment.pk }} ({{ info.assignment.sbmlType }})</span>
        </div>
    </div>

    <div
        class="data"
        v-if="
            info.conversionFactor != null &&
            (info.conversionFactor.sid ||
                info.conversionFactor.value ||
                info.conversionFactor.units)
        "
    >
        <div class="label">
            <strong>Conversion Factor:</strong>
            <div class="p-mb-4">
                <ul title="Conversion Factor">
                    <li v-if="info.conversionFactor.sid">
                        sid: {{ info.conversionFactor.sid }}
                    </li>
                    <li v-if="info.conversionFactor.value">
                        value: {{ info.conversionFactor.value }}
                    </li>
                    <li v-if="info.conversionFactor.units">
                        units: {{ info.conversionFactor.units }}
                    </li>
                </ul>
            </div>
        </div>
    </div>

    <div class="data" v-if="info.fbc && (info.fbc.formula || info.fbc.charge)">
        <div class="label">
            <strong>FBC Data:</strong>
            <div class="p-mb-4">
                <ul title="FBC Data">
                    <li v-if="info.fbc.formula">formula: {{ info.fbc.formula }}</li>
                    <li v-if="info.fbc.charge">charge: {{ info.fbc.charge }}</li>
                </ul>
            </div>
        </div>
    </div>

    <div class="p-grid col-12">
        <div class="col-sm-4 data" v-if="info.reactant && info.reactant.length">
            <div class="label">
                <strong>reactant:</strong>
            </div>
            <div class="p-ml-0">
                <SBMLLink
                    v-for="reactant in info.reactant"
                    :key="reactant"
                    :pk="reactant"
                    :sbmlType="String('Reaction')"
                />
            </div>
        </div>
        <div class="col-sm-4 data" v-if="info.product && info.product.length">
            <div class="label">
                <strong>product:</strong>
            </div>
            <div class="p-ml-0">
                <SBMLLink
                    v-for="product in info.product"
                    :key="product"
                    :pk="product"
                    :sbmlType="String('Reaction')"
                />
            </div>
        </div>

        <div class="col-sm-4 data" v-if="info.modifier && info.modifier.length">
            <div class="label">
                <strong>modifier:</strong>
            </div>
            <div class="p-ml-0">
                <SBMLLink
                    v-for="modifier in info.modifier"
                    :key="modifier"
                    :pk="modifier"
                    :sbmlType="String('Reaction')"
                />
            </div>
        </div>
    </div>-->
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
