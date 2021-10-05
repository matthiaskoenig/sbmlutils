<template>
    <div ref="parameterDiv" class="scrollable">
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

            <Column sortable class="column" field="id" header="id">
                <template #body="props">
                    <strong><code>{{ props.data.id }}</code></strong>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="name"
                header="name"
            ></Column>
            <Column sortable class="column" field="port" header="port">
                <template #body="props">
                    <span v-if="props.data.port != null">
                        <font-awesome-icon icon="plug" :title="props.data.port.pk.split(':')[1]"/>
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="constant"
                header="constant"
                bodyStyle="text-align: center"
            >
                <template #body="props">
                    <boolean-symbol :value="props.data.constant" />
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="value"
                header="value"
            ></Column>
            <Column sortable class="column" field="units" header="units">
                <template #body="props">
                    <span v-if="props.data.units != null">
                        <katex :mathStr="props.data.units" class="katex_unit"/>
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="derivedUnits"
                header="derivedUnits"
            >
                <template #body="props">
                    <span v-if="props.data.derivedUnits != null">
                        <katex :mathStr="props.data.derivedUnits" class="katex_unit" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="assignment"
                header="assignment"
            >
                <template #body="props">
                    <span v-if="props.data.assignment != null">
                        <span v-if="props.data.assignment != null">
                            <katex :mathStr="props.data.assignment.math" />
                        </span>
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
            default: String("Parameter"),
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

    mixins: [tableMixin("Parameter")],
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
