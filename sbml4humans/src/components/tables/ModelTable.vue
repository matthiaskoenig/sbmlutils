<template>
    <div ref="modelDiv" class="scrollable">
        <strong class="sbmlType">
            <font-awesome-icon :icon="`${icon}`" class="mr-1" />
            Models
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
                        <span v-if="object.id != null"
                            ><strong>{{ object.id }}</strong></span
                        >
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

<script>
import store from "@/store/index";
import icons from "@/data/fontAwesome";
import colorScheme from "@/data/colorScheme";
import { defineComponent } from "vue";

import "datatables.net-buttons-bs4";
import $ from "jquery";

export default defineComponent({
    props: {
        listOfPKs: {
            type: Array,
            default: Array,
        },
    },

    created() {
        $(document).ready(() => {
            $("table").DataTable();
        });
    },

    computed: {
        objects() {
            let listOfObjects = [];
            const allObjectsMap = store.state.allObjectsMap;

            this.listOfPKs.forEach((pk) => {
                listOfObjects.push(allObjectsMap[pk]);
            });

            return listOfObjects;
        },

        color() {
            return colorScheme.componentColor["Model"];
        },

        icon() {
            return icons.icons["Model"];
        },
    },

    methods: {
        openComponent(pk) {
            store.dispatch("pushToHistoryStack", pk);
        },
    },

    watch: {
        listOfPKs(pks) {
            if (pks.length == 0) {
                this.$refs["modelDiv"].style.display = "none";
            } else {
                this.$refs["modelDiv"].style.display = "block";
            }
        },
    },
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
