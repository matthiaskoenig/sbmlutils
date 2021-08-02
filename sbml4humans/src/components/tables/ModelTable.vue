<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            :style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsibleModel"
            role="button"
        >
            <i :class="`fas fa-${icon} mr-1`"></i> ListOfModels
        </strong>

        <table
            class="
                table table-striped table-bordered table-sm table-condensed table-hover
                compact
            "
            id="collapsibleModel"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">substance Units</th>
                    <th scope="col">time Units</th>
                    <th scope="col">length Units</th>
                    <th scope="col">area Units</th>
                    <th scope="col">volume Units</th>
                    <th scope="col">extent Units</th>
                    <th scope="col">conversion Factor</th>
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
                        <span v-if="object.substanceUnits != null">{{
                            object.substanceUnits
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.timeUnits != null">{{
                            object.timeUnits
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.lengthUnits != null">{{
                            object.lengthUnits
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.areaUnits != null">{{
                            object.areaUnits
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.volumeUnits != null">{{
                            object.volumeUnits
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.extentUnits != null">{{
                            object.extentUnits
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.conversionFactor != null">{{
                            object.conversionFactor
                        }}</span>
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
            return colorScheme.componentColor["Model"];
        },

        icon(): string {
            return icons.icons["Model"];
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
