<template>
    <!-- Port Reference -->
    <div class="data" v-if="info.portRef">
        <div class="label"><strong>Port Reference:</strong> {{ info.portRef }}</div>
    </div>

    <!-- ID Reference -->
    <div class="data" v-if="info.idRef">
        <div class="label"><strong>ID Reference:</strong> {{ info.idRef }}</div>
    </div>

    <!-- Unit Reference -->
    <div class="data" v-if="info.unitRef">
        <div class="label"><strong>Unit Reference:</strong> {{ info.unitRef }}</div>
    </div>

    <!-- Meta ID Reference -->
    <div class="data" v-if="info.metaIdRef">
        <div class="label">
            <strong>Meta ID Reference:</strong> {{ info.metaIdRef }}
        </div>
    </div>

    <!-- Referenced Element -->
    <div class="data" v-if="info.referencedElement">
        <div class="label">
            <strong>Referenced Element:</strong> {{ info.referencedElement.element }}
            <span v-if="info.referencedElement.elementId"
                >(ID: {{ info.referencedElement.elementId }})</span
            >
        </div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.Model,
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
