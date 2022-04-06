<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.message != null">
                <td class="label-td"><div class="label">message</div></td>
                <td>{{ info.message }}</td>
            </tr>
            <tr v-if="info.math != null">
                <td class="label-td"><div class="label">math</div></td>
                <td><katex :mathStr="info.math" /></td>
            </tr>
        </tbody>
    </table>

    <!-- <div class="data" v-if="info.math != null">
        <div class="label">
            <strong>math:</strong>
            <katex :mathStr="info.math" />
        </div>
    </div>

    <div class="data" v-if="info.message != null">
        <div class="label"><strong>message:</strong>{{ info.message }}</div>
    </div> -->
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of Constraint objects.
 */
export default defineComponent({
    components: {
        Katex,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Constraint,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
