<template>
    <button
        class="btn btn-info p-d-flex p-mx-2 p-py-1"
        v-on:click="menuVisible = !menuVisible"
    >
        <i class="fa fa-filter p-mr-2 p-mt-1" style="color: black" />
        <span class="filter-label">Filter&nbsp;{{ filterFraction }}</span>
    </button>

    <div class="filter" v-if="menuVisible" v-on:click="menuVisible = !menuVisible">
        <p class="p-ml-4 text-dark">Click on a tag to hide that SBML component</p>
        <div class="tag-list">
            <!-- Selectively Displaying Filter buttons for all SBML Types  -->
            <div
                class="p-d-flex"
                v-for="sbmlType in sbmlTypes"
                :key="sbmlType"
                v-on:click="menuVisible = !menuVisible"
            >
                <div class="selector" v-if="counts[sbmlType] > 0">
                    <div
                        class="tag"
                        :ref="sbmlType"
                        :style="`background-color: ${
                            visibility[sbmlType] ? colors[sbmlType] : '#f5f5f5'
                        }; color: ${visibility[sbmlType] ? '#000000' : '#d3d3d3'}`"
                        v-on:click="alterVisibility(sbmlType)"
                    >
                        {{ sbmlType }}
                    </div>
                </div>
                <sup v-if="counts[sbmlType] > 0">
                    <div
                        :ref="`${sbmlType}Badge`"
                        class="badge"
                        :style="`background-color: ${
                            visibility[sbmlType] ? '#000000' : '#f5f5f5'
                        }; color: ${visibility[sbmlType] ? '#ffffff' : '#a9a9a9'}`"
                    >
                        {{ counts[sbmlType] }}
                    </div>
                </sup>
            </div>
        </div>

        <!-- Buttons for select all and de-select all -->
        <div class="master-select" v-on:click="menuVisible = !menuVisible">
            <!-- Select All -->
            <button ref="select" class="btn btn-info p-mx-1" v-on:click="selectAll()">
                <div class="label">Select All</div>
            </button>

            <!-- De-select All -->
            <button
                ref="de-select"
                class="btn btn-info p-mx-1"
                v-on:click="deSelectAll()"
            >
                <div class="label">De-Select All</div>
            </button>
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
    data(): Record<string, unknown> {
        return {
            menuVisible: {
                type: Boolean,
                default: false,
            },
        };
    },

    mounted(): void {
        this.$data["menuVisible"] = false;
    },

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
        currentModel(): string {
            return store.state.currentModel;
        },

        /**
         * Reactively returns the count of each SBML component from Vuex state/localStorage.
         */
        counts(): Record<string, number> {
            return store.getters.counts;
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

        /**
         * Calculates and displays the fraction of SBML objects filtered in the report.
         */
        filterFraction(): string {
            let totalComponents = 0;
            let filteredComponents = 0;

            // calulating the total SBML objects and the number of filtered objects.
            for (let component in this.counts) {
                totalComponents += this.counts[component];
                if (this.visibility[component]) {
                    filteredComponents += this.counts[component];
                }
            }

            // show the filter fraction only if some objects have been actually filtered
            if (filteredComponents > 0) {
                return String("(" + filteredComponents + "/" + totalComponents + ")");
            }

            return "";
        },
    },
});
</script>

<style lang="scss" scoped>
.btn {
    width: max-content;
    font-size: 14px;
}

.btn:focus {
    outline: none;
    box-shadow: none;
}

.filter {
    position: absolute;
    width: 50%;
    height: max-content;
    top: 66px;

    margin: 0 auto;
    padding: 1% 1%;

    border-radius: 10px;

    align-content: center;
    background-color: white;
    box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
    z-index: 1;
}

.selector {
    margin-left: 5px;
    margin-bottom: 13px;
    display: flex;
}

.tag {
    margin-bottom: 3px;
    padding: 2px 5px;

    border-radius: 5px;

    font-size: small;
}

.tag:hover {
    cursor: pointer;
}

.tag:focus {
    outline: none;
    box-shadow: none;
}

.tag-list {
    width: 100%;
    height: 100%;

    margin: 0 auto;
    padding: 1% 1%;

    display: flex;
    flex-wrap: wrap;
}

.badge {
    min-width: 20px;
    width: fit-content;
    height: 20px;
    padding-left: 5px;
    padding-right: 5px;

    border-radius: 20px;

    // stick to the button
    margin-left: -10px;
    margin-top: -5px;

    font-size: small;
    font-weight: 400;
    text-align: center;

    color: white;
    background-color: black;
}

.master-select {
    display: flex;
    flex-direction: row;
    width: max-content;
    margin-left: auto;
    margin-right: auto;
    flex-wrap: wrap;
}

.label {
    margin-top: auto;
    margin-bottom: auto;
    margin-left: 5px;
}

.fa {
    font-size: 18px;
}
</style>
