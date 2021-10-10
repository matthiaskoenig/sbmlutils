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
            <Column sortable class="column" field="reversible" header="reversible">
                <template #body="props">
                    <BooleanSymbol :value="props.data.reversible" />
                </template>
            </Column>
            <Column sortable class="column" field="compartment" header="compartment" />
            <Column sortable class="column" field="equation" header="equation">
                <template #body="props">
                    <span v-html="props.data.equation" />
                </template>
            </Column>
            <Column sortable class="column" field="fast" header="fast">
                <template #body="props">
                    <BooleanSymbol :value="props.data.fast" />
                </template>
            </Column>
            <Column sortable class="column" field="kineticLaw" header="math">
                <template #body="props">
                    <Katex
                        v-if="
                            props.data.kineticLaw != null &&
                            props.data.kineticLaw.math != null
                        "
                        :mathStr="props.data.kineticLaw.math"
                    />
                </template>
            </Column>
            <Column field="kineticLaw" header="derivedUnits" sortable class="column">
                <template #body="props">
                    <TemplateUnits
                        v-if="props.data.kineticLaw != null"
                        :units="props.data.kineticLaw.derivedUnits"
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
import TemplateId from "@/components/tables/TemplateId.vue";
import TemplateUnits from "@/components/tables/TemplateUnits.vue";

export default defineComponent({
    components: {
        TemplateId,
        TemplateUnits,
        BooleanSymbol,
    },
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
