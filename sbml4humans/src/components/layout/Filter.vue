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

<script>
import store from "@/store/index";
import listOfSBMLTypes from "@/data/listOfSBMLTypes";
import colorScheme from "@/data/colorScheme";

export default {
    methods: {
        /**
         * Update the visibility of a specific component button.
         * @param component
         */
        alterVisibility(component) {
            let visibility = this.visibility;
            visibility[component] = !visibility[component];

            store.dispatch("updateVisibility", visibility);
        },

        /**
         * Change visibility and update state.
         */
        selectAll() {
            let visibility = this.visibility;
            // make visibility of all SBML components "true"
            for (let component in visibility) {
                visibility[component] = true;
            }

            store.dispatch("updateVisibility", visibility);
        },

        deSelectAll() {
            let visibility = this.visibility;
            // make visibility of all SBML components "false"
            for (let component in visibility) {
                visibility[component] = false;
            }

            store.dispatch("updateVisibility", visibility);
        },
    },

    data() {
        return {};
    },

    computed: {
        counts() {
            return store.state.counts;
        },

        visibility() {
            return store.state.visibility;
        },

        sbmlTypes() {
            return listOfSBMLTypes.listOfSBMLTypes;
        },

        colors() {
            return colorScheme.componentColor;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Filter.scss";
</style>
