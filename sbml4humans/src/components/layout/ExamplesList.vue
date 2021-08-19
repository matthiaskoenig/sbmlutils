<template>
    <h1>Examples</h1>

    <OrderList v-model="examples" listStyle="height:auto" dataKey="vin">
        <template #header>
            List of Examples
        </template>

        <template #item="slotProps">
              <example
                :key="slotProps.item.id"
                :example="slotProps.item"
            />

        </template>
    </OrderList>

    <loading parent="example" />
</template>

<script lang="ts">
import store from "@/store/index";
import { defineComponent } from "@vue/runtime-core";

/* Components */
import Example from "@/components/layout/Example.vue";
import Loading from "@/components/layout/Loading.vue";

/**
 * Component to display list of all example models fetched from API.
 */
export default defineComponent({
    components: {
        Example,
        Loading,
    },

    created(): void {
        store.dispatch("fetchExamples");
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
</style>
