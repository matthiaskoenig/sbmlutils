<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.symbol != null">
                <td class="label-td"><div class="label">symbol</div></td>
                <td>{{ info.symbol }}</td>
            </tr>
            <tr v-if="info.math != null">
                <td class="label-td"><div class="label">math</div></td>
                <td><katex :mathStr="info.math" /></td>
            </tr>
            <tr v-if="info.derivedUnits != null">
                <td class="label-td"><div class="label">derivedUnits</div></td>
                <td><katex :mathStr="info.derivedUnits" /></td>
            </tr>
        </tbody>
    </table>

    <!-- <div class="data" v-if="info.symbol != null">
        <div class="label"><strong>symbol:</strong> {{ info.symbol }}</div>
    </div>

    <div class="data" v-if="info.math != null">
        <div class="label"><strong>math:</strong> {{ info.math }}</div>
    </div>

    <div class="data" v-if="info.derivedUnits != null">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex :mathStr="info.derivedUnits" />
        </div>
    </div> -->
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Parameter objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.InitialAssignment,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
