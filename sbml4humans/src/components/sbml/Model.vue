<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.substanceUnits != null">
                <td class="label-td"><div class="label">substanceUnits</div></td>
                <td>{{ info.substanceUnits }}</td>
            </tr>
            <tr v-if="info.timeUnits != null">
                <td class="label-td"><div class="label">timeUnits</div></td>
                <td>{{ info.timeUnits }}</td>
            </tr>
            <tr v-if="info.lengthUnits != null">
                <td class="label-td"><div class="label">lengthUnits</div></td>
                <td>{{ info.lengthUnits }}</td>
            </tr>
            <tr v-if="info.areaUnits != null">
                <td class="label-td"><div class="label">areaUnits</div></td>
                <td>{{ info.areaUnits }}</td>
            </tr>
            <tr v-if="info.volumeUnits != null">
                <td class="label-td"><div class="label">volumeUnits</div></td>
                <td>{{ info.volumeUnits }}</td>
            </tr>
            <tr v-if="info.extentUnits != null">
                <td class="label-td"><div class="label">extentUnits</div></td>
                <td>{{ info.extentUnits }}</td>
            </tr>
            <tr v-if="info.conversionFactor != null">
                <td class="label-td"><div class="label">conversionFactor</div></td>
                <td>{{ info.conversionFactor }}</td>
            </tr>
        </tbody>
    </table>

    <!-- <div class="data" v-if="info.substanceUnits != null">
        <div class="label">
            <strong>Substance Units:</strong> {{ info.substanceUnits }}
        </div>
    </div>

    <div class="data" v-if="info.timeUnits != null">
        <div class="label"><strong>timeUnits:</strong> {{ info.timeUnits }}</div>
    </div>

    <div class="data" v-if="info.lengthUnits != null">
        <div class="label"><strong>lengthUnits:</strong> {{ info.lengthUnits }}</div>
    </div>

    <div class="data" v-if="info.areaUnits != null">
        <div class="label"><strong>areaUnits:</strong> {{ info.areaUnits }}</div>
    </div>

    <div class="data" v-if="info.volumeUnits != null">
        <div class="label"><strong>volumeUnits:</strong> {{ info.volumeUnits }}</div>
    </div>

    <div class="data" v-if="info.extentUnits != null">
        <div class="label"><strong>extentUnits:</strong> {{ info.extentUnits }}</div>
    </div>

    <div class="data" v-if="info.conversionFactor != null">
        <div class="label">
            <strong>conversionFactor:</strong> {{ info.conversionFactor }}
        </div>
    </div> -->
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Model objects.
 */
export default defineComponent({
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
