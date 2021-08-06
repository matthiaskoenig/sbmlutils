<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.label != null">
                <td class="label-td"><div class="label">label</div></td>
                <td>{{ info.label }}</td>
            </tr>
            <tr v-if="info.associatedSpecies != null">
                <td class="label-td"><div class="label">associatedSpecies</div></td>
                <td>{{ info.associatedSpecies }}</td>
            </tr>
        </tbody>
    </table>

    <!-- <div class="data" v-if="info.label != null">
        <div class="label"><strong>label:</strong> {{ info.label }}</div>
    </div>

    <div class="data" v-if="info.associatedSpecies != null">
        <div class="label">
            <strong>associatedSpecies:</strong> {{ info.associatedSpecies }}
        </div>
    </div> -->
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of GeneProduct objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.GeneProduct,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
