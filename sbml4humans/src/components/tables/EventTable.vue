<template>
    <div ref="eventDiv" class="scrollable">
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
            <Column field="useValuesFromTriggerTime" header="useValuesFromTriggerTime">
                <template #body="props">
                    <span v-if="props.data.useValuesFromTriggerTime != null">
                        <boolean :value="props.data.useValuesFromTriggerTime" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="trigger"
                header="triggerMath"
            >
                <template #body="props">
                    <span v-if="props.data.trigger.math != null">
                        <katex :mathStr="props.data.trigger.math" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="trigger"
                header="triggerPersistent"
            >
                <template #body="props">
                    <span v-if="props.data.trigger.persistent != null">
                        <boolean :value="props.data.trigger.persistent" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="priority"
                header="priority"
            >
                <template #body="props">
                    <span v-if="props.data.priority != null">
                        <katex :mathStr="props.data.priority" />
                    </span>
                </template>
            </Column>
            <Column sortable class="column" field="delay" header="delay">
                <template #body="props">
                    <span v-if="props.data.delay != null">
                        <katex :mathStr="props.data.delay" />
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

import Boolean from "@/components/layout/BooleanSymbol.vue";

export default defineComponent({
    components: {
        Boolean,
    },

    props: {
        listOfPKs: {
            type: Array,
            default: Array,
        },
        sbmlType: {
            type: String,
            default: String("Event"),
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

    mixins: [tableMixin("Event")],
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
