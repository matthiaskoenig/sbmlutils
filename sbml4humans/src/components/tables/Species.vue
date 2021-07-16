<template>
    <div class="w-100">
        <h2
            class="sbmlType"
            v-bind:style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleSpecies"
            role="button"
        >
            ListOfSpecies
        </h2>

        <table class="table table-striped table-bordered" id="collapsibleSpecies">
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">initialAmount</th>
                    <th scope="col">initialConcentration</th>
                    <th scope="col">substanceUnits</th>
                    <th scope="col">hasOnlySubstanceUnits</th>
                    <th scope="col">boundaryCondition</th>
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
                        <span v-if="object.initialAmount">{{
                            object.initialAmount
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.initialConcentration">{{
                            object.initialConcentration
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.substanceUnits">{{
                            object.substanceUnits
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.hasOnlySubstanceUnits">
                            <boolean-symbol
                                v-bind:value="object.hasOnlySubstanceUnits"
                            ></boolean-symbol
                        ></span>
                    </td>
                    <td>
                        <span v-if="object.boundaryCondition">{{
                            object.boundaryCondition
                        }}</span>
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
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

export default defineComponent({
    components: {
        katex: Katex,
        "boolean-symbol": BooleanSymbol,
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
            return colorScheme.componentColor["Species"];
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
    padding: 2px 5px;
}

.table {
    overflow-x: scroll;
}
</style>
