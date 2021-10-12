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
            <Column
                sortable
                class="column"
                field="substanceUnits"
                header="substance Units"
            >
                <template #body="props">
                    <TemplateUnits :units="props.data.substanceUnits" />
                </template>
            </Column>
            <Column sortable class="column" field="timeUnits" header="time Units">
                <template #body="props">
                    <TemplateUnits :units="props.data.timeUnits" />
                </template>
            </Column>
            <Column sortable class="column" field="lengthUnits" header="length Units">
                <template #body="props">
                    <TemplateUnits :units="props.data.lengthUnits" />
                </template>
            </Column>
            <Column sortable class="column" field="areaUnits" header="area Units">
                <template #body="props">
                    <TemplateUnits :units="props.data.areaUnits" />
                </template>
            </Column>
            <Column sortable class="column" field="volumeUnits" header="volume Units">
                <template #body="props">
                    <TemplateUnits :units="props.data.volumeUnits" />
                </template>
            </Column>
            <Column sortable class="column" field="extentUnits" header="extent Units">
                <template #body="props">
                    <TemplateUnits :units="props.data.extentUnits" />
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="conversionFactor"
                header="conversion Factor"
            >
                <template #body="props">
                    <TemplateConversionFactor
                        :conversionFactor="props.data.conversionFactor"
                    />
                </template>
            </Column>
        </DataTable>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import tableMixin from "@/mixins/tableMixin";
import { defineComponent } from "@vue/runtime-core";
import TemplateId from "@/components/tables/TemplateId.vue";
import TemplateUnits from "@/components/tables/TemplateUnits.vue";
import TemplateConversionFactor from "@/components/tables/TemplateConversionFactor.vue";

export default defineComponent({
    components: {
        TemplateId,
        TemplateUnits,
        TemplateConversionFactor,
    },
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
