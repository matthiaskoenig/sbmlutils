<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.units != null">
                <td class="label-td"><div class="label">units</div></td>
                <td><katex :mathStr="info.units" /></td>
            </tr>
        </tbody>
    </table>
</template>

<script>
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of UnitDefinition objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.UnitDefinition,
        },
    },

    components: {
        Katex,
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
