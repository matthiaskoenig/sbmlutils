<template>
    <div>
        <div class="content-section introduction">
            <div class="feature-intro">
                <h1>DataTable</h1>
                <p>DataTable displays data in tabular format.</p>
            </div>
            <AppDemoActions />
        </div>

        <div class="content-section implementation">
            <div class="card">
                <DataTable
                    :value="customers"
                    :paginator="true"
                    class="p-datatable-customers"
                    :rows="10"
                    dataKey="id"
                    :rowHover="true"
                    v-model:selection="selectedCustomers"
                    v-model:filters="filters"
                    filterDisplay="menu"
                    :loading="loading"
                    paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
                    :rowsPerPageOptions="[10, 25, 50]"
                    currentPageReportTemplate="Showing {first} to {last} of {totalRecords} entries"
                    :globalFilterFields="[
                        'name',
                        'country.name',
                        'representative.name',
                        'status',
                    ]"
                    responsiveLayout="scroll"
                >
                    <template #header>
                        <div class="p-d-flex p-jc-between p-ai-center">
                            <h5 class="p-m-0">Customers</h5>
                            <span class="p-input-icon-left">
                                <i class="pi pi-search" />
                                <InputText
                                    v-model="filters['global'].value"
                                    placeholder="Keyword Search"
                                />
                            </span>
                        </div>
                    </template>
                    <template #empty> No customers found. </template>
                    <template #loading> Loading customers data. Please wait. </template>
                    <Column selectionMode="multiple" style="min-width: 3rem"></Column>
                    <Column
                        field="name"
                        header="Name"
                        sortable
                        style="min-width: 14rem"
                    >
                        <template #body="{ data }">
                            {{ data.name }}
                        </template>
                        <template #filter="{ filterModel }">
                            <InputText
                                type="text"
                                v-model="filterModel.value"
                                class="p-column-filter"
                                placeholder="Search by name"
                            />
                        </template>
                    </Column>
                    <Column
                        field="country.name"
                        header="Country"
                        sortable
                        filterMatchMode="contains"
                        style="min-width: 14rem"
                    >
                        <template #body="{ data }">
                            <img
                                src="public/sbmlutils-logo-60.png"
                                :class="'flag flag-' + data.country.code"
                                width="30"
                            />
                            <span class="image-text">{{ data.country.name }}</span>
                        </template>
                        <template #filter="{ filterModel }">
                            <InputText
                                type="text"
                                v-model="filterModel.value"
                                class="p-column-filter"
                                placeholder="Search by country"
                            />
                        </template>
                    </Column>
                </DataTable>
            </div>
        </div>
    </div>
</template>

<script>
import CustomerService from "./CustomerService.js";
import { FilterMatchMode, FilterOperator } from "primevue/api";
export default {
    data() {
        return {
            customers: null,
            selectedCustomers: null,
            filters: {
                global: { value: null, matchMode: FilterMatchMode.CONTAINS },
                name: {
                    operator: FilterOperator.AND,
                    constraints: [
                        { value: null, matchMode: FilterMatchMode.STARTS_WITH },
                    ],
                },
                "country.name": {
                    operator: FilterOperator.AND,
                    constraints: [
                        { value: null, matchMode: FilterMatchMode.STARTS_WITH },
                    ],
                },
                representative: { value: null, matchMode: FilterMatchMode.IN },
                date: {
                    operator: FilterOperator.AND,
                    constraints: [{ value: null, matchMode: FilterMatchMode.DATE_IS }],
                },
                balance: {
                    operator: FilterOperator.AND,
                    constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }],
                },
                status: {
                    operator: FilterOperator.OR,
                    constraints: [{ value: null, matchMode: FilterMatchMode.EQUALS }],
                },
                activity: { value: null, matchMode: FilterMatchMode.BETWEEN },
                verified: { value: null, matchMode: FilterMatchMode.EQUALS },
            },
            loading: true,
            representatives: [
                { name: "Amy Elsner", image: "amyelsner.png" },
                { name: "Anna Fali", image: "annafali.png" },
                { name: "Asiya Javayant", image: "asiyajavayant.png" },
                { name: "Bernardo Dominic", image: "bernardodominic.png" },
                { name: "Elwin Sharvill", image: "elwinsharvill.png" },
                { name: "Ioni Bowcher", image: "ionibowcher.png" },
                { name: "Ivan Magalhaes", image: "ivanmagalhaes.png" },
                { name: "Onyama Limba", image: "onyamalimba.png" },
                { name: "Stephen Shaw", image: "stephenshaw.png" },
                { name: "XuXue Feng", image: "xuxuefeng.png" },
            ],
            statuses: [
                "unqualified",
                "qualified",
                "new",
                "negotiation",
                "renewal",
                "proposal",
            ],
        };
    },
    created() {
        this.customerService = new CustomerService();
    },
    mounted() {
        this.customers = this.customerService.getCustomersLarge();
        this.customers.forEach((customer) => (customer.date = new Date(customer.date)));
        this.loading = false;
    },
    methods: {
        formatDate(value) {
            return value.toLocaleDateString("en-US", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
            });
        },
        formatCurrency(value) {
            return value.toLocaleString("en-US", {
                style: "currency",
                currency: "USD",
            });
        },
    },
};
</script>

<style lang="scss" scoped>
::v-deep(.p-paginator) {
    .p-paginator-current {
        margin-left: auto;
    }
}
::v-deep(.p-progressbar) {
    height: 0.5rem;
    background-color: #d8dadc;
    .p-progressbar-value {
        background-color: #607d8b;
    }
}
::v-deep(.p-datepicker) {
    min-width: 25rem;
    td {
        font-weight: 400;
    }
}
::v-deep(.p-datatable.p-datatable-customers) {
    .p-datatable-header {
        padding: 1rem;
        text-align: left;
        font-size: 1.5rem;
    }
    .p-paginator {
        padding: 1rem;
    }
    .p-datatable-thead > tr > th {
        text-align: left;
    }
    .p-datatable-tbody > tr > td {
        cursor: auto;
    }
    .p-dropdown-label:not(.p-placeholder) {
        text-transform: uppercase;
    }
}
</style>
