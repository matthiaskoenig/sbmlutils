<template>
    <div ref="compartmentDiv" class="scrollable">
        <DataTable
            :value="objects"
            :paginator="objects.length > 10"
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
                <div class="p-d-flex p-jc-between p-ai-center">
                    <span class="sbmlType">
                        <font-awesome-icon
                            :icon="`${icon}`"
                            :fixed-width="true"
                            class="p-mr-1"
                        />
                        {{ sbmlType === "Species" ? sbmlType : sbmlType + "s" }} ({{
                            count
                        }})
                    </span>
                    <span class="p-input-icon-left p-ml-auto">
                        <i class="pi pi-search" />
                        <InputText
                            v-model="filters['global'].value"
                            class="searchBar"
                            placeholder="Search"
                        />
                    </span>
                </div>
            </template>

            <Column sortable style="width: max-content" field="id" header="id">
                <template #body="props">
                    <strong><code>{{ props.data.id }}</code></strong>
                </template>
            </Column>
            <Column
                sortable
                style="width: max-content"
                field="name"
                header="name"
            ></Column>
            <Column sortable style="width: fit-content" field="port" header="port">
                <template #body="slotProps">
                    <span v-if="slotProps.data.port != null">
                        <font-awesome-icon icon="plug" :title="slotProps.data.port.pk.split(':')[1]"/>
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: max-content"
                field="constant"
                header="constant"
                bodyStyle="text-align: center"
            >
                <template #body="slotProps">
                    <boolean-symbol :value="slotProps.data.constant" />
                </template>
            </Column>
            <Column
                sortable
                style="width: max-content"
                field="spatialDimensions"
                header="dimensions"
            ></Column>
            <Column
                sortable
                style="width: max-content"
                field="size"
                header="size"
            ></Column>
            <Column sortable style="width: max-content" field="units" header="units">
                <template #body="slotProps">
                    <span v-if="slotProps.data.units != null">
                        <katex :mathStr="slotProps.data.units" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: max-content"
                field="derivedUnits"
                header="derived Units"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.derivedUnits != null">
                        <katex :mathStr="slotProps.data.derivedUnits" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: max-content"
                field="assignment"
                header="assignment"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.assignment != null">
                        <katex :mathStr="slotProps.data.assignment.math" />
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
            default: String("Compartment"),
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

    mixins: [tableMixin("Compartment")],
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
