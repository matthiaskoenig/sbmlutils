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
                <td><katex :mathStr="info.derivedUnits" class="katex_unit" /></td>
            </tr>
        </tbody>
    </table>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of Parameter objects.
 */
export default defineComponent({
    components: {
        Katex,
    },

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
