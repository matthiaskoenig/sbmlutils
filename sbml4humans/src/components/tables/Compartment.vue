<template>
    <div class="mb-8">
        <h2
            class="sbmlType"
            v-bind:style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleCompartment"
            role="button"
        >
            ListOfCompartments
        </h2>

        <table class="table table-striped table-bordered" id="collapsibleCompartment">
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">spatialDimensions</th>
                    <th scope="col">size</th>
                    <th scope="col">constant</th>
                    <th scope="col">units</th>
                    <th scope="col">derivedUnits</th>
                    <th scope="col">assignment</th>
                </tr>
            </thead>
            <tbody class="table-body">
                <tr v-for="object in objects" v-bind:key="object">
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
                        <span v-if="object.spatialDimensions">{{
                            object.spatialDimensions
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.size">{{ object.size }}</span>
                    </td>
                    <td>
                        <span v-if="object.constant">{{ object.constant }}</span>
                    </td>
                    <td>
                        <span v-if="object.units">
                            <katex v-bind:mathStr="object.units"></katex>
                        </span>
                    </td>
                    <td>
                        <span v-if="object.derivedUnits">
                            <katex v-bind:mathStr="object.derivedUnits"></katex>
                        </span>
                    </td>
                    <td>
                        <span v-if="object.assignment"
                            >{{ object.assignment.pk }} ({{
                                object.assignment.sbmlType
                            }})</span
                        >
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
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
            return colorScheme.componentColor["Compartment"];
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
.sbmlType {
    width: max-content;
    margin-top: 20px;
    padding: 2px 5px;
}
</style>
