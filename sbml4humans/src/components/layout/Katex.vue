<template>
    <div class="katex ml-4" v-html="katexMathHTML"></div>
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

    computed: {
        /**
         * Renders the raw math string into Latex format using the Katex module.
         */
        katexMathHTML(): string {
            return katex.renderToString(this.mathStr, {
                throwOnError: false,
                output: "mathml",
            });
        },
    },
});
</script>

<style lang="scss" scoped>
/*@font-face {
    font-family: "Open-Sans";
    src: url("https://fonts.googleapis.com/css2?family=Roboto&display=swap")
        format("woff2");
}*/
</style>
