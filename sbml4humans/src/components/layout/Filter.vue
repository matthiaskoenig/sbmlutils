<template>
    <div class="filter">
        <div class="tag-list">
            <!-- Selectively Displaying Filter buttons for all SBML Types  -->
            <div class="d-flex" v-for="sbmlType in sbmlTypes" v-bind:key="sbmlType">
                <div class="selector" v-if="counts[sbmlType] > 0">
                    <div
                        class="tag"
                        v-bind:ref="sbmlType"
                        v-bind:style="`background-color: ${
                            visibility[sbmlType] ? colors[sbmlType] : '#f5f5f5'
                        }; color: ${visibility[sbmlType] ? '#000000' : '#d3d3d3'}`"
                        v-on:click="alterVisibility(sbmlType)"
                    >
                        {{ sbmlType }}
                    </div>
                </div>
                <sup v-if="counts[sbmlType] > 0">
                    <div
                        v-bind:ref="`${sbmlType}Badge`"
                        class="badge"
                        v-bind:style="`background-color: ${
                            visibility[sbmlType] ? '#000000' : '#f5f5f5'
                        }; color: ${visibility[sbmlType] ? '#ffffff' : '#a9a9a9'}`"
                    >
                        {{ counts[sbmlType] }}
                    </div>
                </sup>
            </div>

            <!-- Buttons for select all and de-select all -->
            <div class="master-select">
                <!-- Select All -->
                <button
                    ref="select"
                    class="tick btn btn-info px-5"
                    v-on:click="selectAll()"
                >
                    <div class="label">Select All</div>
                </button>

                <!-- De-select All -->
                <button
                    ref="de-select"
                    class="tick btn btn-info px-5 ml-4"
                    v-on:click="deSelectAll()"
                >
                    <div class="label">De-Select All</div>
                </button>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import store from "@/store/index";
import listOfSBMLTypes from "@/data/listOfSBMLTypes";
import colorScheme from "@/data/colorScheme";
import { defineComponent } from "vue";

/**
 * Component to display buttons to filter SBML components in the generated report.
 */
export default defineComponent({
    methods: {
        /**
         * Update the visibility of a specific component button.
         * @param component the SBML component for which its button's visibility has to be updated
         */
        alterVisibility(component: string): void {
            let visibility = this.visibility;
            visibility[component] = !visibility[component];

            store.dispatch("updateVisibility", visibility);
        },

        /**
         * Change visibility of all components to true and update state.
         */
        selectAll(): void {
            let visibility = this.visibility;
            for (let component in visibility) {
                visibility[component] = true;
            }

            store.dispatch("updateVisibility", visibility);
        },

        /**
         * Change visibility of all components to false and update state.
         */
        deSelectAll(): void {
            let visibility = this.visibility;
            for (let component in visibility) {
                visibility[component] = false;
            }

            store.dispatch("updateVisibility", visibility);
        },
    },

    computed: {
        /**
         * Reactively returns the count of each SBML component from Vuex state/localStorage.
         */
        counts(): Record<string, number> {
            return store.state.counts;
        },

        /**
         * Reactively returns the visibility of each SBML component from Vuex state/localStorage.
         */
        visibility(): Record<string, boolean> {
            return store.state.visibility as { [key: string]: boolean };
        },

        /**
         * Returns a list of all SBML types.
         */
        sbmlTypes(): Array<string> {
            return listOfSBMLTypes.listOfSBMLTypes;
        },

        /**
         * Returns the color scheme defined for SBML components.
         */
        colors(): Record<string, string> {
            return colorScheme.componentColor;
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Filter.scss";
</style>