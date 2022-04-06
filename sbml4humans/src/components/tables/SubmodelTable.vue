<template>
    <div ref="submodelDiv" class="scrollable">
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
                    <font-awesome-icon
                        :icon="`${icon}`"
                        :fixed-width="true"
                        class="p-mr-1"
                    />
                    {{ header }}
                </div>
            </template>
            <Column sortable class="column" field="id" header="id">
                <template #body="props">
                    <TemplateId :data="props.data" />
                </template>
            </Column>
            <Column sortable class="column" field="name" header="name" />
            <Column sortable class="column" field="modelRef" header="modelRef" />
            <Column
                sortable
                class="column"
                field="timeConversion"
                header="timeConversion"
            />
            <Column
                sortable
                class="column"
                field="extentConversion"
                header="extentConversion"
            />
        </DataTable>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import tableMixin from "@/mixins/tableMixin";
import { defineComponent } from "@vue/runtime-core";
import TemplateId from "@/components/tables/TemplateId.vue";

export default defineComponent({
    components: {
        TemplateId,
    },
    props: {
        listOfPKs: {
            type: Array,
            default: Array,
        },
        sbmlType: {
            type: String,
            default: String("Submodel"),
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

    mixins: [tableMixin("Submodel")],
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
