<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.variable != null">
                <td class="label-td"><div class="label">variable</div></td>
                <td>{{ info.variable }}</td>
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

    <!-- <div class="data" v-if="info.sid != null">
        <div class="label"><strong>variable:</strong> {{ info.sid }}</div>
    </div>

    <div class="data" v-if="info.math != null">
        <div class="label">
            <strong>math:</strong>
            <katex :mathStr="info.math" />
        </div>
    </div>

    <div class="data" v-if="info.derivedUnits != null">
        <div class="label">
            <strong>derivedUnits:</strong>
            <katex :mathStr="info.derivedUnits" class="katex_unit" />
        </div>
    </div> -->
</template>

<script>
import TYPES from "@/data/sbmlComponents";

export default {
    props: {
        info: TYPES.AlgebraicRule,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
