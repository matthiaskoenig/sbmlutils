<template>
    <!-- Port Reference -->
    <div class="data" v-if="info.portRef">
        <div class="label"><strong>portRef:</strong> {{ info.portRef }}</div>
    </div>

    <!-- ID Reference -->
    <div class="data" v-if="info.idRef">
        <div class="label"><strong>idRef:</strong> {{ info.idRef }}</div>
    </div>

    <!-- Unit Reference -->
    <div class="data" v-if="info.unitRef">
        <div class="label"><strong>unitRef:</strong> {{ info.unitRef }}</div>
    </div>

    <!-- Meta ID Reference -->
    <div class="data" v-if="info.metaIdRef">
        <div class="label"><strong>metaIdRef:</strong> {{ info.metaIdRef }}</div>
    </div>

    <!-- Referenced Element -->
    <div class="data" v-if="info.referencedElement">
        <div class="label">
            <strong>referencedElement:</strong> {{ info.referencedElement.element }}
            <span v-if="info.referencedElement.elementId"
                >(elementId: {{ info.referencedElement.elementId }})</span
            >
        </div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";
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
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
