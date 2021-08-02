<template>
    <div class="xml-container">
        <div
            v-on:click="visible = !visible"
            :title="visible ? 'Hide JSON' : 'Show JSON'"
            class="d-flex"
            style="cursor: pointer"
        >
            <i :class="`fas fa-${visible ? 'minus' : 'plus'}-circle mt-1 mr-1`"></i>
            <span>JSON</span>
        </div>
        <div>
            <pre v-if="visible" class="xml-text">
                {{ json }}
            </pre>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "vue";

/**
 * Component for rendering JSON/SBML.
 */
export default defineComponent({
    props: {
        json: {
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
         * Update the current json displayed
         */
        updateModalJSON() {
            store.dispatch("updateJSON", this.json);
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
