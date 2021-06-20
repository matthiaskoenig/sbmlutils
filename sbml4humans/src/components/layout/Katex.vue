<template>
    <div ref="katexEl" class="katex ml-4"></div>
</template>

<script lang="ts">
import katex from "katex";
import { defineComponent } from "vue";

/**
 * Component to render math using Katex.
 */
export default defineComponent({
    props: {
        mathStr: {
            type: String,
            default: "",
        },
    },

    /**
     * Renders the raw math string into Latex format using the Katex module.
     */
    mounted() {
        let katexEl = this.$refs["katexEl"] as HTMLDivElement;
        return katex.render(this.mathStr, katexEl, {
            throwOnError: false,
            output: "mathml",
        });
    },
});
</script>

<style lang="scss" scoped>
@import url("https://cdn.jsdelivr.net/npm/katex@0.13.11/dist/katex.css");

.katex {
    font-size: 1em;
}
</style>
