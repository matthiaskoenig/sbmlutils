<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            data-toggle="collapse"
            href="#collapsibleCompartment"
            role="button"
        >
            <i :class="`table-header fas fa-${icon} mr-1`"></i> ListOfCompartments
        </strong>

        <table
            class="table table-striped table-bordered table-sm table-condensed compact"
            id="collapsibleCompartment"
            ref="dataTable"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">spatial Dimensions</th>
                    <th scope="col">size</th>
                    <th scope="col">constant</th>
                    <th scope="col">units</th>
                    <th scope="col">derived Units</th>
                    <th scope="col">assignment</th>
                </tr>
            </thead>
            <tbody class="table-body">
                <tr
                    v-for="object in objects"
                    :key="object"
                    class="links"
                    v-on:click="openComponent(object.pk)"
                >
                    <td>
                        <span v-if="object.id != null">{{ object.id }}</span>
                    </td>
                    <td>
                        <span v-if="object.name != null">{{ object.name }}</span>
                    </td>
                    <td>
                        <span v-if="object.spatialDimensions != null">{{
                            object.spatialDimensions
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.size != null">{{ object.size }}</span>
                    </td>
                    <td class="text-center align-middle">
                        <span v-if="object.constant != null">
                            <boolean-symbol
                                v-if="object.constant === Boolean(true)"
                                :value="object.constant"
                            />
                            <boolean-symbol v-else :value="Boolean(false)" />
                        </span>
                    </td>
                    <td>
                        <span v-if="object.units != null">
                            <katex :mathStr="object.units" />
                        </span>
                    </td>
                    <td>
                        <span v-if="object.derivedUnits != null">
                            <katex :mathStr="object.derivedUnits" />
                        </span>
                    </td>
                    <td>
                        <span v-if="object.assignment != null"
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

export default defineComponent({
    components: {
        Katex,
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
            return colorScheme.componentColor["Compartment"];
        },

        icon(): string {
            return icons.icons["Compartment"];
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