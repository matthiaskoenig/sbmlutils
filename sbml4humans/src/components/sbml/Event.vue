<template>
    <!-- Use Values From Trigger Time -->
    <div class="data" v-if="info.useValuesFromTriggerTime != null">
        <div class="label">
            <strong>useValuesFromTriggerTime:</strong>
            {{ info.useValuesFromTriggerTime }}
        </div>
    </div>

    <!-- Trigger -->
    <div class="data" v-if="info.trigger != null">
        <div class="label">
            <strong>trigger:</strong>
            <div class="ml-4">
                <div v-if="info.trigger.math != null">
                    math:
                    <katex :mathStr="info.trigger.math"></katex>
                </div>
                <div v-if="info.trigger.initialValue != null">
                    initialValue: {{ info.trigger.initialValue }}
                </div>
                <div v-if="info.trigger.peristent != null">
                    persistent: {{ info.trigger.peristent }}
                </div>
            </div>
        </div>
    </div>

    <!-- Priority -->
    <div class="data" v-if="info.priority != null">
        <div class="label">
            <strong>priority:</strong>
            <katex :mathStr="info.priority"></katex>
        </div>
    </div>

    <!-- Delay -->
    <div class="data" v-if="info.delay != null">
        <div class="label">
            <strong>delay:</strong>
            <katex :mathStr="info.delay"></katex>
        </div>
    </div>

    <!-- List of Event Assignments -->
    <div
        class="data"
        v-if="
            info.listOfEventAssignments != null &&
            info.listOfEventAssignments.length > 0
        "
    >
        <div class="label">
            <strong>listOfEventAssignments:</strong>
            <div class="ml-4">
                <ul title="List of Event Assignments">
                    <li v-for="eva in info.listOfEventAssignments" :key="eva.variable">
                        <div v-if="eva.variable">variable: {{ eva.variable }}</div>
                        <div v-if="eva.math">
                            math:
                            <katex :mathStr="eva.math"></katex>
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
