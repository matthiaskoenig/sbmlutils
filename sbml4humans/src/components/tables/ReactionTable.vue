<template>
    <div ref="reactionDiv" class="scrollable">
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
                field="name"
                header="name"
                sortable
                class="column"
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
                field="reversible"
                header="reversible"
                bodyStyle="text-align: center"
            >
                <template #body="props">
                    <boolean-symbol :value="props.data.reversible" />
                </template>
            </Column>
            <Column
                field="compartment"
                header="compartment"
                sortable
                class="column"
            ></Column>
            <Column
                sortable
                class="column"
                field="equation"
                header="equation"
            >
                <template #body="props">
                    <span v-html="props.data.equation" />
                </template>
            </Column>
            <Column
                sortable
                class="column"
                field="fast"
                header="fast"
                bodyStyle="text-align: center"
            >
                <template #body="props">
                    <boolean-symbol :value="props.data.fast" />
                </template>
            </Column>
            <Column
                field="kineticLaw"
                header="math"
                sortable
                class="column"
            >
                <template #body="props">
                    <span
                        v-if="
                            props.data.kineticLaw != null &&
                            props.data.kineticLaw.math != null
                        "
                    >
                        <katex :mathStr="props.data.kineticLaw.math" />
                    </span>
                </template>
            </Column>
            <Column
                field="kineticLaw"
                header="derivedUnits"
                sortable
                class="column"
            >
                <template #body="props">
                    <span
                        v-if="
                            props.data.kineticLaw != null &&
                            props.data.kineticLaw.derivedUnits != null
                        "
                    >
                        <katex :mathStr="props.data.kineticLaw.derivedUnits" class="katex_unit"/>
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
            default: String("Reaction"),
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

    mixins: [tableMixin("Reaction")],
});
</script>

<style lang="scss">
@import "@/assets/styles/scss/SBaseTable.scss";
</style>
