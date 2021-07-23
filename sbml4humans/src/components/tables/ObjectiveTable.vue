<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            :style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleObjective"
            role="button"
        >
           <i :class="`fas fa-${icon} mr-1`"></i> ListOfObjectives
        </strong>

        <table
            class="table table-striped table-bordered table-sm table-condensed"
            id="collapsibleObjective"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">type</th>
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
                        <span v-if="object.type">
                            {{ object.type }}
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

export default defineComponent({
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
            return colorScheme.componentColor["Objective"];
        },

        icon(): string {
            return icons.icons["Objective"];
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
