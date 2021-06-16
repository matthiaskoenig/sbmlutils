<template>
    <span v-html="katexMath"></span>
</template>

<script lang="ts">
import katex from "katex";

/**
 * Component to render math using Katex.
 */
export default {
    props: {
        mathStr: {
            type: String,
        },
    },

    computed: {
        /**
         * Renders the raw math string into Latex format using the Katex module.
         */
        katexMath(): string {
            return katex.renderToString(this.mathStr, {
                throwOnError: false,
            });
        },
    },
};
</script>

<style lang="scss" scoped></style>
