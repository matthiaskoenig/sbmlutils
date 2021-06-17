<template>
    <div class="xml-container">
        <button
            v-if="xml"
            type="button"
            class="btn btn-info px-5"
            data-toggle="modal"
            data-target="#exampleModalScrollable"
            v-on:click="hideUnhideXML()"
        >
            View XML
        </button>
        <pre ref="xmlContent" class="xml-text" style="display: none">{{
            formattedXML
        }}</pre>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import xmlFormatter from "xml-formatter";
import { defineComponent } from "vue";

/**
 * Component for rendering XML/SBML.
 */
export default defineComponent({
    props: {
        xml: {
            type: String,
            required: true,
        },
    },

    methods: {
        /**
         * Update the current xml code to be displayed in the XML container.
         */
        updateModalXML() {
            store.dispatch("updateXML", this.xml);
        },

        hideUnhideXML(): void {
            this.updateModalXML();
            let xmlContent: HTMLDivElement = this.$refs["xmlContent"] as HTMLDivElement;
            if (xmlContent.style.display === "none") {
                xmlContent.style.display = "block";
            } else {
                xmlContent.style.display = "none";
            }
        },
    },

    computed: {
        /**
         * Formats and returns the raw XML string passed from the parent into
         * pretty-printed form.
         */
        formattedXML(): string {
            let formattedXML: string;
            formattedXML = this.xml != null ? xmlFormatter(this.xml) : "";
            return formattedXML;
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/XMLContainer.scss";
</style>
