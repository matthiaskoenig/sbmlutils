<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.units != null">
                <td class="label-td"><div class="label">units</div></td>
                <td><katex :mathStr="info.units" class="katex_unit" /></td>
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
        </tbody>
    </table>
</template>

<script>
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";
import SBMLLink from "@/components/layout/SBMLLink.vue";

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
        SBMLLink,
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
