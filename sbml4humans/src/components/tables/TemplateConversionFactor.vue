<template>
    <span v-if="conversionFactor != null && conversionFactor.sid">
        {{ conversionFactor.sid }} = {{ conversionFactor.value }}
        {{ conversionFactor.units }}
    </span>
</template>

<script>
import { defineComponent } from "@vue/runtime-core";
export default defineComponent({
    props: {
        conversionFactor: {
            type: Object,
        },
    },
});
</script>

<style scoped></style>
