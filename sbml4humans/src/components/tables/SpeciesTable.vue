<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            :style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleSpecies"
            role="button"
        >
            <i :class="`fas fa-${icon} mr-1`"></i> ListOfSpecies
        </strong>

        <table
            class="table table-striped table-bordered table-sm table-condensed"
            id="collapsibleSpecies"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">initial Amount</th>
                    <th scope="col">initial Concentration</th>
                    <th scope="col">substance Units</th>
                    <th scope="col">hasOnly SubstanceUnits</th>
                    <th scope="col">boundary Condition</th>
                    <th scope="col">constant</th>
                    <th scope="col">units</th>
                    <th scope="col">derived Units</th>
                    <th scope="col">assignment</th>
                </tr>
            </thead>
            <tbody class="table-body">
                <tr v-for="object in objects" :key="object">
                    <td>
                        <span
                            v-if="object.id"
                            class="links"
                            v-on:click="openComponent(object.pk)"
                        >
                            {{ object.id }}
                        </span>
                    </td>
                    <td>
                        <span v-if="object.name">{{ object.name }}</span>
                    </td>
                    <td>
                        <span v-if="object.initialAmount">
                            {{ object.initialAmount }}
                        </span>
                    </td>
                    <td>
                        <span v-if="object.initialConcentration">
                            {{ object.initialConcentration }}
                        </span>
                    </td>
                    <td>
                        <span v-if="object.substanceUnits">{{
                            object.substanceUnits
                        }}</span>
                    </td>
                    <td class="text-center align-middle">
                        <boolean-symbol
                            v-if="object.hasOnlySubstanceUnits"
                            :value="object.hasOnlySubstanceUnits"
                        />
                    </td>
                    <td>
                        <span v-if="object.boundaryCondition">{{
                            object.boundaryCondition
                        }}</span>
                    </td>
                    <td class="text-center align-middle">
                        <boolean-symbol
                            v-if="object.constant"
                            :value="object.constant"
                        />
                        <boolean-symbol v-else :value="Boolean(false)" />
                    </td>
                    <td>
                        <katex v-if="object.units" :mathStr="object.units" />
                    </td>
                    <td>
                        <span v-if="object.derivedUnits">
                            <katex :mathStr="object.derivedUnits"></katex>
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
import icons from "@/data/fontAwesome";
import colorScheme from "@/data/colorScheme";
import { defineComponent } from "vue";

import Katex from "@/components/layout/Katex.vue";
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

// use a mixin to define the reusable parts once;
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

        icon(): string {
            return icons.icons["Species"];
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

.scrollable {
    width: 100%;
    overflow-x: scroll;
}
</style>
