<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.useValuesFromTriggerTime != null">
                <td class="label-td">
                    <div class="label">useValuesFromTriggerTime</div>
                </td>
                <td>{{ info.useValuesFromTriggerTime }}</td>
            </tr>
            <tr v-if="info.trigger != null">
                <td class="label-td"><div class="label">trigger</div></td>
                <td>
                    <div v-if="info.trigger.math != null">
                        math:
                        <katex :mathStr="info.trigger.math" />
                    </div>
                    <div v-if="info.trigger.initialValue != null">
                        initialValue: {{ info.trigger.initialValue }}
                    </div>
                    <div v-if="info.trigger.peristent != null">
                        persistent: {{ info.trigger.peristent }}
                    </div>
                </td>
            </tr>
            <tr v-if="info.priority != null">
                <td class="label-td"><div class="label">priority</div></td>
                <td><katex :mathStr="info.priority" /></td>
            </tr>
            <tr v-if="info.delay != null">
                <td class="label-td"><div class="label">delay</div></td>
                <td><katex :mathStr="info.delay" /></td>
            </tr>
            <tr
                v-if="
                    info.listOfEventAssignments != null &&
                    info.listOfEventAssignments.length > 0
                "
            >
                <td class="label-td"><div class="label">eventAssignments</div></td>
                <td>
                    <ul title="List of Event Assignments">
                        <li
                            v-for="eva in info.listOfEventAssignments"
                            :key="eva.variable"
                        >
                            <div v-if="eva.variable">variable: {{ eva.variable }}</div>
                            <div v-if="eva.math">
                                math:
                                <katex :mathStr="eva.math" />
                            </div>
                        </li>
                    </ul>
                </td>
            </tr>
        </tbody>
    </table>

    <!--
    <div class="data" v-if="info.useValuesFromTriggerTime != null">
        <div class="label">
            <strong>useValuesFromTriggerTime:</strong>
            {{ info.useValuesFromTriggerTime }}
        </div>
    </div>

    <div class="data" v-if="info.trigger != null">
        <div class="label">
            <strong>trigger:</strong>
            <div class="p-ml-4">
                <div v-if="info.trigger.math != null">
                    math:
                    <katex :mathStr="info.trigger.math" />
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

    <div class="data" v-if="info.priority != null">
        <div class="label">
            <strong>priority:</strong>
            <katex :mathStr="info.priority" />
        </div>
    </div>

    <div class="data" v-if="info.delay != null">
        <div class="label">
            <strong>delay:</strong>
            <katex :mathStr="info.delay" />
        </div>
    </div>

    <div
        class="data"
        v-if="
            info.listOfEventAssignments != null &&
            info.listOfEventAssignments.length > 0
        "
    >
        <div class="label">
            <strong>listOfEventAssignments:</strong>
            <div class="p-ml-4">
                <ul title="List of Event Assignments">
                    <li v-for="eva in info.listOfEventAssignments" :key="eva.variable">
                        <div v-if="eva.variable">variable: {{ eva.variable }}</div>
                        <div v-if="eva.math">
                            math:
                            <katex :mathStr="eva.math" />
                        </div>
                    </li>
                </ul>
            </div>
        </div>
    </div> -->
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
        Katex,
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
