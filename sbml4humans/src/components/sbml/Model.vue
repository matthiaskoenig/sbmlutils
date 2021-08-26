<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.substanceUnits != null">
                <td class="label-td"><div class="label">substanceUnits</div></td>
                <td>
                    <span v-if="info.substanceUnits != null">
                        <katex :mathStr="info.substanceUnits" />
                    </span>
                </td>
            </tr>
            <tr v-if="info.timeUnits != null">
                <td class="label-td"><div class="label">timeUnits</div></td>
                <td>
                    <span v-if="info.timeUnits != null">
                        <katex :mathStr="info.timeUnits" />
                    </span>
                </td>
            </tr>
            <tr v-if="info.lengthUnits != null">
                <td class="label-td"><div class="label">lengthUnits</div></td>
                <td>
                    <span v-if="info.lengthUnits != null">
                        <katex :mathStr="info.lengthUnits" />
                    </span>
                </td>
            </tr>
            <tr v-if="info.areaUnits != null">
                <td class="label-td"><div class="label">areaUnits</div></td>
                <td>
                    <span v-if="info.areaUnits != null">
                        <katex :mathStr="info.areaUnits" />
                    </span>
                </td>
            </tr>
            <tr v-if="info.volumeUnits != null">
                <td class="label-td"><div class="label">volumeUnits</div></td>
                <td>
                    <span v-if="info.volumeUnits != null">
                        <katex :mathStr="info.volumeUnits" />
                    </span>
                </td>
            </tr>
            <tr v-if="info.extentUnits != null">
                <td class="label-td"><div class="label">extentUnits</div></td>
                <td>
                    <span v-if="info.extentUnits != null">
                        <katex :mathStr="info.extentUnits" />
                    </span>
                </td>
            </tr>
            <tr v-if="info.conversionFactor != null">
                <td class="label-td"><div class="label">conversionFactor</div></td>
                <td>
                    <span v-if="info.conversionFactor != null">
                        <katex :mathStr="info.conversionFactor" />
                    </span>
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of Model objects.
 */
export default defineComponent({
    components: {
        Katex,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Model,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
