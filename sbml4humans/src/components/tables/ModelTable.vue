<template>
    <div ref="modelDiv" class="scrollable">
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
                    <strong class="sbmlType">
                        <font-awesome-icon :icon="`${icon}`" class="p-mr-1" />
                        {{ sbmlType === "Species" ? sbmlType : sbmlType + "s" }} ({{
                            count
                        }})
                    </strong>
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

            <Column sortable style="width: fit-content" field="id" header="id">
                <template #body="props">
                    <strong><code>{{ props.data.id }}</code></strong>
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="name"
                header="name"
            ></Column>
            <Column
                sortable
                style="width: fit-content"
                field="substanceUnits"
                header="substance Units"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.substanceUnits != null">
                        <katex :mathStr="slotProps.data.substanceUnits" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="timeUnits"
                header="time Units"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.timeUnits != null">
                        <katex :mathStr="slotProps.data.timeUnits" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="lengthUnits"
                header="length Units"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.lengthUnits != null">
                        <katex :mathStr="slotProps.data.lengthUnits" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="areaUnits"
                header="area Units"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.areaUnits != null">
                        <katex :mathStr="slotProps.data.areaUnits" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="volumeUnits"
                header="volume Units"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.volumeUnits != null">
                        <katex :mathStr="slotProps.data.volumeUnits" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="extentUnits"
                header="extent Units"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.extentUnits != null">
                        <katex :mathStr="slotProps.data.extentUnits" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="conversionFactor"
                header="conversion Factor"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.conversionFactor != null">
                        <katex :mathStr="slotProps.data.conversionFactor" />
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
            default: String("Model"),
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

    mixins: [tableMixin("Model")],
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
