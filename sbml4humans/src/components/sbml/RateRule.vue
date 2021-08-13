<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.sid != null">
                <td class="label-td"><div class="label">variable</div></td>
                <td>{{ info.sid }}</td>
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
</template>

<script>
import TYPES from "@/data/sbmlComponents";

export default {
    props: {
        info: TYPES.RateRule,
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
