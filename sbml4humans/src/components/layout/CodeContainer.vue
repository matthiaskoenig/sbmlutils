<template>
    <div class="xml-container">
        <div
            ::v-tooltip="visible ? 'Hide Code' : 'Show Code'"
            class="p-d-flex"
            style="cursor: pointer"
        >
            <div class="p-mr-4" v-if="info.xml != null" v-on:click="toggleToXML()">
                <font-awesome-icon icon="code" class="p-mr-1" />
                <span><strong>XML</strong></span>
            </div>

            <div v-on:click="toggleToJSON()">
                <i class="fas fa-braces p-mr-1"></i>
                <span><strong>JSON</strong></span>
            </div>
        </div>
        <div v-if="visible">
            <pre class="xml-text">{{ language === 0 ? formattedXML : info }}</pre>
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
        info: {
            type: Object,
            required: false,
        },
    },

    data(): Record<string, unknown> {
        return {
            visible: false,
            language: 0, // 0 for XML, 1 for JSON
        };
    },

    methods: {
        toggleToXML(): void {
            if (this.language === 1) {
                this.visible = true;
            } else {
                this.visible = !this.visible;
            }
            this.language = 0;
        },

        toggleToJSON(): void {
            if (this.language === 0) {
                this.visible = true;
            } else {
                this.visible = !this.visible;
            }
            this.language = 1;
        },
    },

    computed: {
        /**
         * Formats and returns the raw XML string passed from the parent into
         * pretty-printed form.
         */
        formattedXML(): string {
            let formattedXML: string;
            formattedXML = xmlFormatter(
                (this.info as unknown as Record<string, unknown>)
                    .xml as unknown as string
            );
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
    font-size: xx-small;
}

.fa-braces:before {
    font-weight: 1000;
    margin-left: 4px;
    content: "{...}";
}
</style>
