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
            <Column sortable class="column" field="value" header="value" />
            <Column sortable class="column" field="units" header="units">
                <template #body="props">
                    <Katex
                        v-if="props.data.units != null"
                        :mathStr="props.data.units"
                        class="katex_unit"
                    />
                </template>
            </Column>
            <Column sortable class="column" field="derivedUnits" header="derivedUnits">
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
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";
import TemplateUnits from "@/components/tables/TemplateUnits.vue";
import TemplateId from "@/components/tables/TemplateId.vue";

export default defineComponent({
    components: {
        BooleanSymbol,
        TemplateUnits,
        TemplateId,
    },
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
