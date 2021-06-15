<!DOCTYPE html>
<template>
    <pre v-html="katexMath"></pre>
</template>

<script>
import katex from "katex";

export default {
    replace: true,
    props: {
        mathStr: String, // comes from the SBase component as of now, hardcoded
    },

    data() {
        return {
            katexStr: String,
        };
    },

    computed: {
        katexMath() {
            return katex.renderToString(this.mathStr, {
                throwOnError: false,
            });
        },
    },
};
</script>

<style lang="scss" scoped></style>
