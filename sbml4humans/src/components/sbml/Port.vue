<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.portRef != null">
                <td class="label-td"><div class="label">portRef</div></td>
                <td>{{ info.portRef }}</td>
            </tr>
            <tr v-if="info.idRef != null">
                <td class="label-td"><div class="label">idRef</div></td>
                <td>{{ info.idRef }}</td>
            </tr>
            <tr v-if="info.unitRef != null">
                <td class="label-td"><div class="label">unitRef</div></td>
                <td>{{ info.unitRef }}</td>
            </tr>
            <tr v-if="info.metaIdRef != null">
                <td class="label-td"><div class="label">metaIdRef</div></td>
                <td>{{ info.metaIdRef }}</td>
            </tr>
            <tr v-if="info.referencedElement != null">
                <td class="label-td"><div class="label">referencedElement</div></td>
                <td>
                    referencedElement: {{ info.referencedElement.element }}
                    <span v-if="info.referencedElement.elementId != null"
                        >(elementId: {{ info.referencedElement.elementId }})</span
                    >
                </td>
            </tr>
        </tbody>
    </table>

    <!-- <div class="data" v-if="info.portRef != null">
        <div class="label"><strong>portRef:</strong> {{ info.portRef }}</div>
    </div>

    <div class="data" v-if="info.idRef != null">
        <div class="label"><strong>idRef:</strong> {{ info.idRef }}</div>
    </div>

    <div class="data" v-if="info.unitRef != null">
        <div class="label"><strong>unitRef:</strong> {{ info.unitRef }}</div>
    </div>

    <div class="data" v-if="info.metaIdRef != null">
        <div class="label"><strong>metaIdRef:</strong> {{ info.metaIdRef }}</div>
    </div>

    <div class="data" v-if="info.referencedElement != null">
        <div class="label">
            <strong>referencedElement:</strong> {{ info.referencedElement.element }}
            <span v-if="info.referencedElement.elementId != null"
                >(elementId: {{ info.referencedElement.elementId }})</span
            >
        </div>
    </div> -->
</template>

<script>
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Port objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.Port,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
