<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            :style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleEvent"
            role="button"
        >
            <i :class="`fas fa-${icon} mr-1`"></i> ListOfEvents
        </strong>

        <table
            class="table table-striped table-bordered table-sm table-condensed"
            id="collapsibleEvent"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">useValuesFromTriggerTime</th>
                    <th scope="col">trigger math</th>
                    <th scope="col">trigger initialValue</th>
                    <th scope="col">trigger persistent</th>
                    <th scope="col">priority</th>
                    <th scope="col">delay</th>
                </tr>
            </thead>
            <tbody class="table-body">
                <tr v-for="object in objects" :key="object">
                    <td>
                        <span
                            v-if="object.id"
                            class="links"
                            v-on:click="openComponent(object.pk)"
                            >{{ object.id }}</span
                        >
                    </td>
                    <td>
                        <span v-if="object.name">{{ object.name }}</span>
                    </td>
                    <td>
                        <span v-if="object.useValuesFromTriggerTime">{{
                            object.useValuesFromTriggerTime
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.trigger && object.trigger.math">
                            <katex :mathStr="object.trigger.math"></katex>
                        </span>
                    </td>
                    <td>
                        <span v-if="object.trigger && object.trigger.initialValue">{{
                            object.trigger.initialValue
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.trigger && object.trigger.persistent">{{
                            object.trigger.persistent
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.priority">
                            <katex :mathStr="object.persistent"></katex>
                        </span>
                    </td>
                    <td>
                        <span v-if="object.delay">
                            <katex :mathStr="object.delay"></katex>
                        </span>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import icons from "@/data/fontAwesome";
import colorScheme from "@/data/colorScheme";
import { defineComponent } from "vue";

import Katex from "@/components/layout/Katex.vue";

export default defineComponent({
    components: {
        katex: Katex,
    },

    props: {
        listOfPKs: {
            type: Array,
            default: Array,
        },
    },

    computed: {
        objects(): Array<Record<string, unknown>> {
            let listOfObjects: Array<Record<string, unknown>> = [];
            const allObjectsMap = store.state.allObjectsMap;

            (this.listOfPKs as Array<string>).forEach((pk) => {
                listOfObjects.push(allObjectsMap[pk]);
            });

            return listOfObjects;
        },

        color(): string {
            return colorScheme.componentColor["Event"];
        },

        icon(): string {
            return icons.icons["Event"];
        },
    },

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
