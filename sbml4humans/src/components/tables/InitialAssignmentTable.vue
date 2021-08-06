<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            data-toggle="collapse"
            href="#collapsibleInitialAssignment"
            role="button"
        >
            <i :class="`fas fa-${icon} mr-1`"></i> ListOfInitialAssignments
        </strong>

        <table
            class="table table-striped table-bordered table-sm table-condensed compact"
            id="collapsibleInitialAssignment"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">variable</th>
                    <th scope="col">math</th>
                    <th scope="col">derivedUnits</th>
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
                        <span v-if="object.variable != null">{{
                            object.variable
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.math != null">
                            <katex :mathStr="object.math" />
                        </span>
                    </td>
                    <td>
                        <span v-if="object.derivedUnits != null">
                            <katex :mathStr="object.derivedUnits" />
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
        Katex,
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
            return colorScheme.componentColor["InitialAssignment"];
        },

        icon(): string {
            return icons.icons["InitialAssignment"];
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