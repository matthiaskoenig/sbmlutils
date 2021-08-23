<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.spatialDimensions != null">
                <td class="label-td"><div class="label">spatialDimensions</div></td>
                <td>{{ info.spatialDimensions }}</td>
            </tr>
            <tr v-if="info.size != null">
                <td class="label-td"><div class="label">size</div></td>
                <td>{{ info.size }}</td>
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
                <td><katex :mathStr="info.units" /></td>
            </tr>
            <tr v-if="info.derivedUnits != null">
                <td class="label-td"><div class="label">derivedUnits</div></td>
                <td><katex :mathStr="info.derivedUnits" /></td>
            </tr>
            <tr v-if="info.assignment != null">
                <td class="label-td"><div class="label">assignment</div></td>
                <td>
                    <SBMLLink
                        :pk="info.assignment.pk"
                        :sbmlType="String(info.assignment.sbmlType)"
                    />
                </td>
            </tr>
            <tr v-if="info.species && info.species.length">
                <td class="label-td"><div class="label">species</div></td>
                <td>
                    <SBMLLink
                        v-for="species in info.species"
                        :key="species"
                        :pk="species"
                        :sbmlType="String('Species')"
                    />
                </td>
            </tr>
            <tr v-if="info.reaction && info.reaction.length">
                <td class="label-td"><div class="label">reaction</div></td>
                <td>
                    <SBMLLink
                        v-for="reaction in info.reaction"
                        :key="reaction"
                        :pk="reaction"
                        :sbmlType="String('Reaction')"
                    />
                </td>
            </tr>
        </tbody>
    </table>

    <!-- <div class="data" v-if="info.spatialDimensions != null">
        <div class="label">
            <strong>spatialDimensions:</strong> {{ info.spatialDimensions }}
        </div>
    </div>

    <div class="data" v-if="info.size != null">
        <div class="label"><strong>size:</strong> {{ info.size }}</div>
    </div>

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

    <div class="data" v-if="info.units != null">
        <div class="label">
            <strong>units:</strong>
            <katex :mathStr="info.units" />
        </div>
    </div>

    <div class="data" v-if="info.derivedUnits != null">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex :mathStr="info.derivedUnits" />
        </div>
    </div>

    <div class="data" v-if="info.assignment != null">
        <div class="label">
            <strong>assignment:</strong>
            <span>{{ info.assignment.pk }} ({{ info.assignment.sbmlType }})</span>
        </div>
    </div>

    <div class="data w-100" v-if="info.species != null">
        <div class="label">
            <strong>relatedSpecies:</strong>
        </div>
        <div class="p-ml-4 tag-list">
            <div v-for="species in info.species" :key="species">
                <SBMLLink :pk="species" :sbmlType="String('Species')" />
            </div>
        </div>
    </div>

    <div class="data w-100" v-if="info.reaction != null">
        <div class="label">
            <strong>relatedReactions:</strong>
        </div>
        <div class="p-ml-4 tag-list">
            <div v-for="reaction in info.reaction" :key="reaction">
                <SBMLLink :pk="reaction" :sbmlType="String('Reaction')" />
            </div>
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
