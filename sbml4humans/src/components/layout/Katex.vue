<template>
    <div>
        Test KaTex
        <div v-html="katexMathHTML"></div>
        </div>
</template>

<script lang="ts">
import katex from "katex";
import {defineComponent} from "vue";

/**
 * Component to render math using Katex.
 */
export default defineComponent({
    props: {
        mathStr: {
            type: String,
        },
    },

    computed: {
        /**
         * Renders the raw math string into Latex format using the Katex module.
         */
        katexMathHTML(): string {
            return katex.renderToString("c = \\pm\\sqrt{a^2 + b^2}", {
                throwOnError: false,
                output: "mathml",
            });

        },
    },
});
</script>

<style lang="scss" scoped></style>
