<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.math != null">
                <td class="label-td"><div class="label">math</div></td>
                <td><katex :mathStr="info.math" /></td>
            </tr>
        </tbody>
    </table>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of FunctionDefinition objects.
 */
export default defineComponent({
    components: {
        Katex,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.FunctionDefinition,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
