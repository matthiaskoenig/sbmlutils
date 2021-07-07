<template>
    <div class="xml-container">
        <div
            v-on:click="visible = !visible"
            :title="visible ? 'Hide SBML' : 'Show SBML'"
        >
            <i v-bind:class="`fa fa-${visible ? 'minus' : 'plus'}-circle`"></i>
        </div>
        <pre v-if="visible" ref="xmlContent" class="xml-text">
            {{ formattedXML }}
        </pre>
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

    data(): Record<string, unknown> {
        return {
            visible: {
                type: Boolean,
                default: true,
            },
        };
    },

    methods: {
        /**
         * Update the current xml displayed
         */
        updateModalXML() {
            store.dispatch("updateXML", this.xml);
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
pre {
    white-space: pre-wrap;
    white-space: -moz-pre-wrap;
    white-space: -pre-wrap;
    white-space: -o-pre-wrap;
    word-wrap: break-word;
}

.xml-container {
    margin-top: 2%;
    display: flex;
    flex-direction: row;
}

.xml-text {
    margin-top: 2%;
    overflow-y: scroll;

    font-family: "Courier New", Courier, monospace;
    font-size: small;
}
</style>
