<template>
    <div class="w-100">
        <h2
            class="sbmlType"
            v-bind:style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleReaction"
            role="button"
        >
            ListOfReactions
        </h2>

        <table class="table table-striped table-bordered" id="collapsibleReaction">
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">reversible</th>
                    <th scope="col">compartment</th>
                    <th scope="col">equation</th>
                    <th scope="col">fast</th>
                    <th scope="col">kineticLaw math</th>
                    <th scope="col">kineticLaw derivedUnits</th>
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
                        <span v-if="object.reversible">{{ object.reversible }}</span>
                    </td>
                    <td>
                        <span v-if="object.compartment">{{ object.compartment }}</span>
                    </td>
                    <td>
                        <span v-if="object.equation" v-html="object.equation"></span>
                    </td>
                    <td>
                        <span v-if="object.fast">{{ object.fast }}</span>
                    </td>
                    <td>
                        <span v-if="object.kineticLaw && object.kineticLaw.math">
                            <katex v-bind:mathStr="object.kineticLaw.math"></katex>
                        </span>
                    </td>
                    <td>
                        <span
                            v-if="object.kineticLaw && object.kineticLaw.derivedUnits"
                        >
                            <katex
                                v-bind:mathStr="object.kineticLaw.derivedUnits"
                            ></katex>
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
            return colorScheme.componentColor["Reaction"];
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
