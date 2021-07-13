<template>
    <div class="mb-8">
        <h2
            class="sbmlType"
            v-bind:style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleAssignmentRule"
            role="button"
        >
            ListOfAssignmentRules
        </h2>

        <table
            class="table table-striped table-bordered"
            id="collapsibleAssignmentRule"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">value</th>
                    <th scope="col">math</th>
                    <th scope="col">derivedUnits</th>
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
                        <span v-if="object.value">{{ object.value }}</span>
                    </td>
                    <td>
                        <span v-if="object.math">
                            <katex v-bind:mathStr="object.id + '=' + object.math"></katex>
                        </span>
                    </td>
                    <td>
                        <span v-if="object.derivedUnits">
                            <katex v-bind:mathStr="object.derivedUnits"></katex>
                        </span>
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
            return colorScheme.componentColor["AssignmentRule"];
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
