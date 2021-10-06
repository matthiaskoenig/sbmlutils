<template>
    <katex v-if="units != null" :mathStr="units" class="katex_unit" />
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";
import Katex from "@/components/layout/Katex.vue";
export default defineComponent({
    components: {
        Katex,
    },
    props: {
        units: {
            type: String,
        },
    },
});
</script>

<style scoped></style>
