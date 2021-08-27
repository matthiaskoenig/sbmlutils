<template>
    <div ref="algebraicRuleDiv" class="scrollable">
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
                        {{ sbmlType === "Species" ? sbmlType : sbmlType + "s" }} ({{ count }})
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
                    <strong>{{ props.data.id }}</strong>
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
                field="value"
                header="value"
            ></Column>
            <Column sortable style="width: fit-content" field="math" header="math">
                <template #body="slotProps">
                    <span v-if="slotProps.data.math != null">
                        <katex :mathStr="slotProps.data.math" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="derivedUnits"
                header="derivedUnits"
            >
                <template #body="slotProps">
                    <span v-if="slotProps.data.derivedUnits != null">
                        <katex :mathStr="slotProps.data.derivedUnits" />
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
            default: String("AlgebraicRule"),
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

    mixins: [tableMixin("AlgebraicRule")],
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
