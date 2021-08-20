<template>
    <div class="p-mt-2">
        <DataTable
            :value="examples"
            :paginator="examples.length > 10"
            :rows="10"
            :rowsPerPageOptions="[10, 25, 50]"
            v-model:filters="filters"
            filterDisplay="menu"
            sortMode="multiple"
            v-if="examples.length > 0"
            style="font-size: 12px"
            class="p-datatable-sbml"
            :globalFilterFields="['global', 'searchUtilField']"
            responsiveLayout="scroll"
            :rowHover="true"
            @row-click="getExample($event.data.id)"
        >
            <template #header class="table-header">
                <div class="p-d-flex p-jc-between p-ai-center">
                    <h1 style="font-size: 2.7em">Examples</h1>
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
            <Column sortable style="width: fit-content" field="id" header="id">
                <template #body="props">
                    <strong>{{ props.data.id }}</strong>
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="name"
                header="name"
            ></Column>
            <Column
                sortable
                style="width: fit-content"
                field="description"
                header="description"
            ></Column>
            <Column
                sortable
                style="width: fit-content"
                field="keywords"
                header="keywords"
            >
                <template #body="props">
                    {{ props.data.keywords.join(",") }}
                </template>
            </Column>
            <Column
                sortable
                style="width: fit-content"
                field="packages"
                header="packages"
            >
                <template #body="props">
                    <span
                        v-for="pkg in props.data.packages"
                        :key="pkg"
                        :class="`package-badge p-mr-1`"
                        :style="`background-color: ${badgeColor[pkg]}; color: ${badgeText[pkg]}`"
                        >{{ pkg }}</span
                    >
                </template>
            </Column>
        </DataTable>

        <loading parent="example" />
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";
import { FilterMatchMode, FilterOperator } from "primevue/api";

/* Components */
import Example from "@/components/layout/Example.vue";
import Loading from "@/components/layout/Loading.vue";

/**
 * Component to display list of all example models fetched from API.
 */
export default defineComponent({
    components: {
        //Example,
        Loading,
    },
    data() {
        return {
            filters: {
                global: { value: null, matchMode: FilterMatchMode.CONTAINS },
                searchUtilField: {
                    operator: FilterOperator.AND,
                    constraints: [{ value: null, matchMode: FilterMatchMode.CONTAINS }],
                },
            },
            badgeColor: {
                distrib: "#5bc0de",
                comp: "#f0ad4e",
                fbc: "#0275d8",
                groups: "#5cb85c",
            },

            badgeText: {
                distrib: "#000000",
                comp: "#000000",
                fbc: "#ffffff",
                groups: "#ffffff",
            },
        };
    },
    created(): void {
        store.dispatch("fetchExamples");
    },

    methods: {
        getExample(exampleId: string): void {
            const payload = {
                exampleId: exampleId,
            };

            store.dispatch("fetchExampleReport", payload);
        },
    },

    computed: {
        /**
         * Reactively returns the list of examples from Vuex state/localStorage.
         */
        examples(): Array<Record<string, unknown>> {
            return store.state.examples;
        },

        /**
         * Reactively returns the loading status of the example(s) from Vuex state/localStorage.
         */
        loading(): boolean {
            return store.state.exampleLoading;
        },
    },
});
</script>

<style lang="scss" scoped>
.badge {
    border-radius: 50%;
    padding: 2px 5px;
    text-align: center;
}

.package-badge {
    border-radius: 10px;
    padding: 2px 5px;
    font-size: 11px;
    font-weight: 600;
}
</style>
