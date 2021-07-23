<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            :style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleParameter"
            role="button"
        >
           <i :class="`fas fa-${icon} mr-1`"></i> ListOfParameters
        </strong>

        <table
            class="table table-striped table-bordered table-sm table-condensed"
            id="collapsibleParameter"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">value</th>
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
                            >{{ object.id }}</span
                        >
                    </td>
                    <td>
                        <span v-if="object.name">{{ object.name }}</span>
                    </td>
                    <td>
                        <span v-if="object.value">{{ object.value }}</span>
                    </td>
                    <td class="text-center align-middle">
                        <span v-if="object.constant"
                            ><boolean-symbol :value="object.constant"></boolean-symbol
                        ></span>

                        <span v-else
                            ><boolean-symbol :value="Boolean(false)"></boolean-symbol
                        ></span>
                    </td>
                    <td>
                        <span v-if="object.units">
                            <katex :mathStr="object.units"></katex>
                        </span>
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

import tableMixin from "@/helpers/tableMixin";

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
            return colorScheme.componentColor["Parameter"];
        },

        icon(): string {
            return icons.icons["Parameter"];
        },
    },

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },

    // computed: {
    //     tableMi(): Record<string, unknown> {
    //         return tableMixin(this.listOfPKs as Array<string>);
    //     },
    // },
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
