<template>
    <!-- Use Values From Trigger Time -->
    <div class="data" v-if="info.useValuesFromTriggerTime">
        <div class="label">
            <strong>useValuesFromTriggerTime:</strong>
            {{ info.useValuesFromTriggerTime }}
        </div>
    </div>

    <!-- Trigger -->
    <div class="data" v-if="info.trigger">
        <div class="label">
            <strong>trigger:</strong>
            <div class="ml-4">
                <div v-if="info.trigger.math">
                    math:
                    <katex v-bind:mathStr="info.trigger.math"></katex>
                </div>
                <div v-if="info.trigger.initialValue">
                    initialValue: {{ info.trigger.initialValue }}
                </div>
                <div v-if="info.trigger.peristent">
                    persistent: {{ info.trigger.peristent }}
                </div>
            </div>
        </div>
    </div>

    <!-- Priority -->
    <div class="data" v-if="info.priority">
        <div class="label">
            <strong>priority:</strong>
            <katex v-bind:mathStr="info.priority"></katex>
        </div>
    </div>

    <!-- Delay -->
    <div class="data" v-if="info.delay">
        <div class="label">
            <strong>delay:</strong>
            <katex v-bind:mathStr="info.delay"></katex>
        </div>
    </div>

    <!-- List of Event Assignments -->
    <div class="data" v-if="info.listOfEventAssignments.length > 0">
        <div class="label">
            <strong>listOfEventAssignments:</strong>
            <div class="ml-4">
                <ul title="List of Event Assignments">
                    <li
                        v-for="eva in info.listOfEventAssignments"
                        v-bind:key="eva.variable"
                    >
                        <div v-if="eva.variable">variable: {{ eva.variable }}</div>
                        <div v-if="eva.math">
                            math:
                            <katex v-bind:mathStr="eva.math"></katex>
                        </div>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import Katex from "@/components/layout/Katex.vue";

/**
 * Component to define display of Event objects.
 */
export default defineComponent({
    components: {
        katex: Katex,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.Event,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
