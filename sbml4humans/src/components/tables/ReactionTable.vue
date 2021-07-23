<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            :style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleReaction"
            role="button"
        >
            <i :class="`fas fa-${icon} mr-1`"></i> ListOfReactions
        </strong>

        <table
            class="table table-striped table-bordered table-sm table-condensed compact"
            id="collapsibleReaction"
        >
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
                <tr v-for="object in objects" :key="object" class="links" v-on:click="openComponent(object.pk)">
                    <td>
                        <span
                            v-if="object.id != null"
                            >{{ object.id }}</span
                        >
                    </td>
                    <td>
                        <span v-if="object.name != null">{{ object.name }}</span>
                    </td>
                    <td class="text-center align-middle">
                        <span v-if="object.reversible != null">
                            <boolean-symbol
                                v-if="object.reversible === Boolean(true)"
                                :value="object.reversible"
                            />
                            <boolean-symbol v-else :value="Boolean(false)" />
                        </span>
                    </td>
                    <td>
                        <span v-if="object.compartment != null">{{
                            object.compartment
                        }}</span>
                    </td>
                    <td>
                        <span
                            v-if="object.equation != null"
                            v-html="object.equation"
                        ></span>
                    </td>
                    <td class="text-center align-middle">
                        <span v-if="object.fast != null">
                            <boolean-symbol
                                v-if="object.fast === Boolean(true)"
                                :value="object.fast"
                            />
                            <boolean-symbol v-else :value="Boolean(false)" />
                        </span>
                    </td>
                    <td>
                        <span
                            v-if="
                                object.kineticLaw != null &&
                                object.kineticLaw.math != null
                            "
                        >
                            <katex :mathStr="object.kineticLaw.math"></katex>
                        </span>
                    </td>
                    <td>
                        <span
                            v-if="
                                object.kineticLaw != null &&
                                object.kineticLaw.derivedUnits != null
                            "
                        >
                            <katex :mathStr="object.kineticLaw.derivedUnits"></katex>
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
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

export default defineComponent({
    components: {
        Katex,
        BooleanSymbol,
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

        icon(): string {
            return icons.icons["Reaction"];
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
