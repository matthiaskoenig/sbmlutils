<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.variable != null">
                <td class="label-td"><div class="label">variable</div></td>
                <td>{{ info.variable }}</td>
            </tr>
            <tr v-if="info.math != null">
                <td class="label-td"><div class="label">math</div></td>
                <td><Katex :mathStr="info.math" /></td>
            </tr>
            <tr v-if="info.derivedUnits != null">
                <td class="label-td"><div class="label">derivedUnits</div></td>
                <td><Katex :mathStr="info.derivedUnits" class="katex_unit" /></td>
            </tr>
        </tbody>
    </table>
</template>

<script>
import TYPES from "@/data/sbmlComponents";
import Katex from "@/components/layout/Katex";

export default {
    components: {
        Katex,
    },
    props: {
        info: TYPES.RateRule,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
