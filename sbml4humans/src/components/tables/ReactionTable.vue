<template>
    <div ref="reactionDiv" class="scrollable">
        <DataTable
            :value="objects"
            :paginator="true"
            :rows="10"
            :rowsPerPageOptions="[10, 25, 50]"
            v-model:filters="filters"
            filterDisplay="menu"
            sortMode="multiple"
            v-if="objects.length > 0"
            style="font-size: 12px"
            class="p-datatable-sbml"
            :globalFilterFields="['global', 'searchUtilField']"
            responsiveLayout="scroll"
            :rowHover="true"
            @row-click="openComponent($event.data.pk)"
        >
            <template #header class="table-header">
                <div class="d-flex p-jc-between p-ai-center">
                    <strong class="sbmlType">
                        <font-awesome-icon :icon="`${icon}`" class="mr-1" />
                        {{ sbmlType === "Species" ? sbmlType : sbmlType + "s" }}
                    </strong>
                    <span class="p-input-icon-left ml-auto">
                        <i class="pi pi-search" />
                        <InputText
                            v-model="filters['global'].value"
                            class="searchBar"
                            placeholder="Search"
                        />
                    </span>
                </div>
            </template>

            <Column sortable style="width: fit-content" field="id" header="id">
                <template #body="props">
                    <strong>{{ props.data.id }}</strong>
                </template>
            </Column>
            <Column
                field="name"
                header="name"
                sortable
                style="width: fit-content"
            ></Column>
            <Column
                sortable
                style="width: fit-content"
                field="reversible"
                header="reversible"
                bodyStyle="text-align: center"
            >
                <template #body="slotProps">
                    <boolean-symbol :value="slotProps.data.reversible" />
                </template>
            </Column>
            <Column
                field="compartment"
                header="compartment"
                sortable
                style="width: fit-content"
            ></Column>
            <Column
                sortable
                style="width: fit-content"
                field="equation"
                header="equation"
            >
                <template #body="slotProps">
                    <span v-html="slotProps.data.equation" />
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="fast"
                header="fast"
                bodyStyle="text-align: center"
            >
                <template #body="slotProps">
                    <boolean-symbol :value="slotProps.data.fast" />
                </template>
            </Column>
            <Column
                field="kineticLaw"
                header="kLaw math"
                sortable
                style="width: fit-content"
            >
                <template #body="slotProps">
                    <span
                        v-if="
                            slotProps.data.kineticLaw != null &&
                            slotProps.data.kineticLaw.math != null
                        "
                    >
                        <katex :mathStr="slotProps.data.kineticLaw.math" />
                    </span>
                </template>
            </Column>
            <Column
                field="kineticLaw"
                header="kLaw derivedUnits"
                sortable
                style="width: fit-content"
            >
                <template #body="slotProps">
                    <span
                        v-if="
                            slotProps.data.kineticLaw != null &&
                            slotProps.data.kineticLaw.derivedUnits != null
                        "
                    >
                        <katex :mathStr="slotProps.data.kineticLaw.derivedUnits" />
                    </span>
                </template>
            </Column>
        </DataTable>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import tableMixin from "@/mixins/tableMixin";
import { defineComponent } from "@vue/runtime-core";

export default defineComponent({
    props: {
        listOfPKs: {
            type: Array,
            default: Array,
        },
        sbmlType: {
            type: String,
            default: String("Reaction"),
        },
    },

    computed: {
        objects(): Array<Record<string, unknown>> {
            const listOfObjects: Array<Record<string, unknown>> = [];
            const allObjectsMap = store.state.allObjectsMap;

            (this.listOfPKs as Array<string>).forEach((pk) => {
                listOfObjects.push(allObjectsMap[pk]);
            });

            return listOfObjects;
        },
    },

    mixins: [tableMixin("Reaction")],
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
