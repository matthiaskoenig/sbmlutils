<template>
    <div ref="compartmentDiv" class="scrollable">
        <DataTable
            :value="objects"
            :paginator="objects.length > 10"
            :rows="10"
            :rowsPerPageOptions="[10, 25, 50]"
            v-model:filters="filters"
            filterDisplay="menu"
            expander
            :autoLayout="true"
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
            <Column sortable class="column" field="constant" header="constant">
                <template #body="props">
                    <BooleanSymbol :value="props.data.constant" />
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="spatialDimensions"
                header="dimensions"
            />
            <Column sortable class="column" field="size" header="size" />
            <Column sortable class="column" field="units" header="units">
                <template #body="props">
                    <TemplateUnits :units="props.data.units" />
                </template>
            </Column>
            <Column sortable class="column" field="derivedUnits" header="derived Units">
                <template #body="props">
                    <TemplateUnits :units="props.data.derivedUnits" />
                </template>
            </Column>
            <Column sortable class="column" field="assignment" header="assignment">
                <template #body="props">
                    <Katex
                        v-if="props.data.assignment != null"
                        :mathStr="props.data.assignment.math"
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
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

export default defineComponent({
    components: {
        BooleanSymbol,
        TemplateId,
        TemplateUnits,
    },
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
