<template>
    <div class="scrollable">
        <strong
            class="sbmlType"
            :style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsiblePort"
            role="button"
        >
            <i :class="`fas fa-${icon} mr-1`"></i> ListOfPorts
        </strong>

        <table
            class="table table-striped table-bordered table-sm table-condensed compact"
            id="collapsiblePort"
        >
            <thead class="thead-dark">
                <tr>
                    <th scope="col">id</th>
                    <th scope="col">name</th>
                    <th scope="col">portRef</th>
                    <th scope="col">idRef</th>
                    <th scope="col">unitRef</th>
                    <th scope="col">metaIdRef</th>
                    <th scope="col">referencedElement</th>
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
                    <td>
                        <span v-if="object.portRef != null">{{ object.portRef }}</span>
                    </td>
                    <td>
                        <span v-if="object.idRef != null">{{ object.idRef }}</span>
                    </td>
                    <td>
                        <span v-if="object.unitRef != null">{{ object.unitRef }}</span>
                    </td>
                    <td>
                        <span v-if="object.metaIdRef != null"
                            >{{ object.metaIdRef }}
                        </span>
                    </td>
                    <td>
                        <span
                            v-if="
                                object.referencedElement != null &&
                                object.referencedElement.elementId != null
                            "
                            >{{ object.referencedElement.elementId }}</span
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
            return colorScheme.componentColor["Port"];
        },

        icon(): string {
            return icons.icons["Port"];
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
