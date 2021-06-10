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
            const xml =
                this.rawXML === "" || this.rawXML === null
                    ? "<xml></xml>"
                    : this.rawXML;
            var formattedXML = xmlFormatter(xml);
            return formattedXML;
        },
    },
}
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/XMLContainer.scss";
</style>
