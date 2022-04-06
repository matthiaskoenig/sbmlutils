<template>
    <span ref="katexEl" class="katex" v-html="katexMath"></span>
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
    computed: {
        katexMath(): string {
            if (this.mathStr === null || this.mathStr === "null") {
                return katex.renderToString("", {
                    throwOnError: false,
                    output: "html",
                });
            } else {
                return katex.renderToString(String(this.mathStr), {
                    throwOnError: false,
                    output: "html",
                });
            }
        },
    },
});
</script>

<style lang="scss" scoped>
.katex {
    font-size: 1em;
}
.katex_unit {
    font-size: 0.8em;
}
</style>
