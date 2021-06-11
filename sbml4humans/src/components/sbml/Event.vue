<template>
    <!-- Use Values From Trigger Time -->
    <div class="data" v-if="info.useValuesFromTriggerTime">
        <div class="label">
            <strong>Use Values From Trigger Time:</strong>
            {{ info.useValuesFromTriggerTime }}
        </div>
    </div>

    <!-- Trigger -->
    <div class="data" v-if="info.trigger">
        <div class="label">
            <strong>Trigger:</strong>
            <div class="ml-4">
                <div v-if="info.trigger.math">
                    Math: <span v-html="info.trigger.math"></span>
                </div>
                <div v-if="info.trigger.initialValue">
                    Initial Value: {{ info.trigger.initialValue }}
                </div>
                <div v-if="info.trigger.peristent">
                    Persistent: {{ info.trigger.peristent }}
                </div>
            </div>
        </div>
    </div>

    <!-- Priority -->
    <div class="data" v-if="info.priority">
        <div class="label">
            <strong>Priority:</strong>
            {{ info.priority }}
        </div>
    </div>

    <!-- Delay -->
    <div class="data" v-if="info.delay">
        <div class="label">
            <strong>Delay:</strong>
            {{ info.delay }}
        </div>
    </div>

    <!-- List of Event Assignments -->
    <div class="data" v-if="info.listOfEventAssignments.length > 0">
        <div class="label">
            <strong>List of Event Assignments:</strong>
            <div class="ml-4">
                <ul title="List of Event Assignments">
                    <li
                        v-for="eva in info.listOfEventAssignments"
                        v-bind:key="eva.variable"
                    >
                        <div v-if="eva.variable">Variable: {{ eva.variable }}</div>
                        <div v-if="eva.math">Math: <span v-html="eva.math"></span></div>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.Event,
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
