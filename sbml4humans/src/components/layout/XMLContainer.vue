<template>
    <div class="xml-container">
        <pre class="xml-text">{{ formattedXML }}</pre>
    </div>
</template>

<script>
import store from "@/store/index";
import xmlFormatter from "xml-formatter";

export default {
    props: {
        xml: String,
    },

    computed: {
        rawXML() {
            return store.state.xml;
        },

        formattedXML() {
            // const xml =
            //     this.rawXML === "" || this.rawXML === null
            //         ? "<xml></xml>"
            //         : this.rawXML;
            var formattedXML = xmlFormatter(this.xml);
            return formattedXML;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/XMLContainer.scss";
</style>
