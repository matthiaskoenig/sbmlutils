<template>
    <katex
        v-if="math != null"
        :mathStr="math"
    />
</template>

<script lang="ts">
import Katex from "@/components/layout/Katex.vue";
import { defineComponent } from "@vue/runtime-core";
export default defineComponent({
    components: {
        Katex,
    },
    props: {
        units: {
            math: String,
        },
    },
});
</script>

<style scoped></style>
