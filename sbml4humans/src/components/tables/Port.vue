<template>
    <div class="mb-8">
        <h2
            class="sbmlType"
            v-bind:style="`background-color: ${color}`"
            data-toggle="collapse"
            href="#collapsiblePort"
            role="button"
        >
            ListOfPorts
        </h2>

        <table class="table table-striped table-bordered" id="collapsiblePort">
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
                <tr v-for="object in objects" v-bind:key="object">
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
                        <span v-if="object.portRef">{{ object.portRef }}</span>
                    </td>
                    <td>
                        <span v-if="object.idRef">{{ object.idRef }}</span>
                    </td>
                    <td>
                        <span v-if="object.unitRef">{{ object.unitRef }}</span>
                    </td>
                    <td>
                        <span v-if="object.metaIdRef">{{ object.metaIdRef }} </span>
                    </td>
                    <td>
                        <span
                            v-if="
                                object.referencedElement &&
                                object.referencedElement.elementId
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
    },

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },
});
</script>

<style lang="scss">
.sbmlType {
    width: max-content;
    margin-top: 20px;
    padding: 2px 5px;
}
</style>
