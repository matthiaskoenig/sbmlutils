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
            <Column
                sortable
                class="column"
                field="substanceUnits"
                header="substance Units"
            >
                <template #body="props">
                    <span v-if="props.data.substanceUnits != null">
                        <katex :mathStr="props.data.substanceUnits" class="katex_unit"  />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="timeUnits"
                header="time Units"
            >
                <template #body="props">
                    <span v-if="props.data.timeUnits != null">
                        <katex :mathStr="props.data.timeUnits" class="katex_unit" />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="lengthUnits"
                header="length Units"
            >
                <template #body="props">
                    <span v-if="props.data.lengthUnits != null">
                        <katex :mathStr="props.data.lengthUnits" class="katex_unit"  />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="areaUnits"
                header="area Units"
            >
                <template #body="props">
                    <span v-if="props.data.areaUnits != null">
                        <katex :mathStr="props.data.areaUnits" class="katex_unit"  />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="volumeUnits"
                header="volume Units"
            >
                <template #body="props">
                    <span v-if="props.data.volumeUnits != null">
                        <katex :mathStr="props.data.volumeUnits" class="katex_unit"  />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="extentUnits"
                header="extent Units"
            >
                <template #body="props">
                    <span v-if="props.data.extentUnits != null">
                        <katex :mathStr="props.data.extentUnits" class="katex_unit"  />
                    </span>
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="conversionFactor"
                header="conversion Factor"
            >
                <template #body="props">
                    <span v-if="props.data.conversionFactor != null && props.data.conversionFactor.sid">
                    {{ props.data.conversionFactor.sid }} = {{ props.data.conversionFactor.value }} {{ props.data.conversionFactor.units }}
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
