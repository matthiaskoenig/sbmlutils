<template>
    <div ref="constraintDiv" class="scrollable">
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
                <div class="p-d-flex p-jc-between p-ai-center sbmlType">
                    <font-awesome-icon :icon="`${icon}`" class="p-mr-1" />
                    {{ sbmlType === "Species" ? sbmlType : sbmlType + "s" }} ({{
                        count
                    }})
                </div>
            </template>

            <Column sortable class="column" field="id" header="id">
                <template #body="props">
                    <strong><code>{{ props.data.id }}</code></strong>
                    <font-awesome-icon
                        v-if="props.data.port != null"
                        icon="plug"
                        :title="props.data.port.pk.split(':')[1]"
                    />
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="name"
                header="name"
            ></Column>
            <Column sortable class="column" field="math" header="math">
                <template #body="props">
                    <span v-if="props.data.math != null">
                        <katex :mathStr="props.data.math" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="message"
                header="message"
            ></Column>
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
            default: String("Constraint"),
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

    mixins: [tableMixin("Constraint")],
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
