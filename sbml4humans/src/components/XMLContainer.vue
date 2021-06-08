<template>
    <div class="xml-container">
        <pre class="xml-text">{{ formattedXML }}</pre>
    </div>
</template>

<script>
import xmlFormatter from "xml-formatter";

export default {
    props: {
        rawXML: String,
    },

    computed: {
        formattedXML() {
            var formattedXML = xmlFormatter(this.rawXML);
            return formattedXML;
        },
    },
}
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/XMLContainer.scss";
</style>
