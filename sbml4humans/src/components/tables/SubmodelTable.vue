<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            data-toggle="collapse"
            href="#collapsibleSubmodel"
            role="button"
        >
            <font-awesome-icon :icon="`${icon}`" class="mr-1" />
            ListOfSubmodels
        </strong>

        <table
            class="
                table table-striped table-bordered table-sm table-condensed table-hover
                compact
            "
            id="collapsibleSubmodel"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">modelRef</th>
                    <th scope="col">timeConversion</th>
                    <th scope="col">extentConversion</th>
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
                        <span v-if="object.modelRef != null">{{
                            object.modelRef
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.timeConversion != null">{{
                            object.timeConversion
                        }}</span>
                    </td>
                    <td>
                        <span v-if="object.extentConversion != null">{{
                            object.extentConversion
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
            return colorScheme.componentColor["Submodel"];
        },

        icon(): string {
            return icons.icons["Submodel"];
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
