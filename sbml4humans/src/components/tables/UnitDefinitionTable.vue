<template>
    <div ref="unitDefinitionDiv" class="scrollable">
        <strong class="sbmlType">
            <font-awesome-icon :icon="`${icon}`" class="mr-1" /> UnitDefinitions
        </strong>

        <table
            class="table table-striped table-bordered table-sm table-condensed compact"
            id="collapsibleUnitDefintion"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">units</th>
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
                        <span v-if="object.id != null"
                            ><strong>{{ object.id }}</strong></span
                        >
                    </td>
                    <td>
                        <span v-if="object.name != null">{{ object.name }}</span>
                    </td>
                    <td>
                        <span v-if="object.units != null">
                            <katex :mathStr="object.units" />
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
            return colorScheme.componentColor["UnitDefinition"];
        },

        icon(): string {
            return icons.icons["UnitDefinition"];
        },
    },

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },

    watch: {
        listOfPKs(pks) {
            if (pks.length == 0) {
                (this.$refs["unitDefinitionDiv"] as HTMLDivElement).style.display =
                    "none";
            } else {
                (this.$refs["unitDefinitionDiv"] as HTMLDivElement).style.display =
                    "block";
            }
        },
    },
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
