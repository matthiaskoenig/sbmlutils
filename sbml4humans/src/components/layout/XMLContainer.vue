<template>
    <div class="xml-container">
        <div
            v-on:click="visible = !visible"
            :title="visible ? 'Hide SBML' : 'Show SBML'"
            class="d-flex"
            style="cursor: pointer"
        >
            <i :class="`fas fa-${visible ? 'minus' : 'plus'}-circle mt-1 mr-1`"></i>
            <span>XML</span>
        </div>
        <div v-if="visible">
            <pre class="xml-text">
                {{ formattedXML }}
            </pre>
        </div>
    </div>
</template>

<script lang="ts">
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

    data(): Record<string, unknown> {
        return {
            visible: {
                type: Boolean,
                default: false,
            },
        };
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
pre {
    white-space: pre-wrap;
    white-space: -moz-pre-wrap;
    white-space: -pre-wrap;
    white-space: -o-pre-wrap;
    word-wrap: break-word;
}

.xml-container {
    margin-top: 2%;
}

.xml-text {
    margin-top: 2%;
    overflow-y: scroll;

    font-family: "Courier New", Courier, monospace;
    font-size: small;
}
</style>
