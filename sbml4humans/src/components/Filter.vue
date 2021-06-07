<template>
    <div class="filter">
        <div class="tag-list">
            <div class="selector">
                <button
                    ref="SBMLDocument"
                    v-if="counts.SBMLDocument > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('SBMLDocument')"
                    :style="`background-color: ${colors.SBMLDocument}`"
                >
                    SBMLDocument
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.SBMLDocument"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="Ports"
                    v-if="counts.Ports > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Port')"
                    :style="`background-color: ${colors.Ports}`"
                >
                    Ports
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Ports"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="Model"
                    v-if="counts.Model > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Model')"
                    :style="`background-color: ${colors.Model}`"
                >
                    Models
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Model"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="FunctionDefinitions"
                    v-if="counts.FunctionDefinitions > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('FunctionDefinitions')"
                    :style="`background-color: ${colors.FunctionDefinitions}`"
                >
                    FunctionDefinitions
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.FunctionDefinitions"
                >
                </a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="UnitDefinitions"
                    v-if="counts.UnitDefinitions > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('UnitDefinitions')"
                    :style="`background-color: ${colors.UnitDefinitions}`"
                >
                    UnitDefinitions
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.UnitDefinitions"
                ></a-badge
            ></sup>

            <div class="selector">
                <button
                    ref="Compartments"
                    v-if="counts.Compartments > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Compartments')"
                    :style="`background-color: ${colors.Compartments}`"
                >
                    Compartments
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Compartments"
                ></a-badge
            ></sup>

            <div class="selector">
                <button
                    ref="Species"
                    v-if="counts.Species > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Species')"
                    :style="`background-color: ${colors.Species}`"
                >
                    Species
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Species"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="Parameters"
                    v-if="counts.Parameters > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Parameters')"
                    :style="`background-color: ${colors.Parameters}`"
                >
                    Parameters
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Parameters"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="Reactions"
                    v-if="counts.Reactions > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Reactions')"
                    :style="`background-color: ${colors.Reactions}`"
                >
                    Reactions
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Reactions"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="Rules"
                    v-if="counts.Rules > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Rules')"
                    :style="`background-color: ${colors.Rules}`"
                >
                    AssignmentRules
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Rules"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="Constraints"
                    v-if="counts.Constraints > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Constraints')"
                    :style="`background-color: ${colors.Constraints}`"
                >
                    Constraints
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Constraints"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="InitialAssignments"
                    v-if="counts.InitialAssignments > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('InitialAssignments')"
                    :style="`background-color: ${colors.InitialAssignments}`"
                >
                    InitialAssignments
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.InitialAssignmens"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="Events"
                    v-if="counts.Events > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Events')"
                    :style="`background-color: ${colors.Events}`"
                >
                    Events
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Events"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="Objectives"
                    v-if="counts.Objectives > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Objectives')"
                    :style="`background-color: ${colors.Objectives}`"
                >
                    Objectives
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Objectives"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="Submodels"
                    v-if="counts.Submodels > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Submodels')"
                    :style="`background-color: ${colors.Submodels}`"
                >
                    Submodels
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.Submodels"
                ></a-badge>
            </sup>

            <div class="selector">
                <button
                    ref="GeneProducts"
                    v-if="counts.GeneProducts > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('GeneProducts')"
                    :style="`background-color: ${colors.GeneProducts}`"
                >
                    GeneProducts
                </button>
            </div>
            <sup>
                <a-badge
                    class="count-badge"
                    :number-style="{ backgroundColor: '#000000' }"
                    v-bind:count="counts.GeneProducts"
                ></a-badge>
            </sup>
        </div>

        <div class="master-select">
            <input ref="select" class="tick" type="checkbox" @click="selectDeselectAll()" />
            <div ref="label" class="label">Select All</div>
        </div>
    </div>
</template>

<script>
import store from "@/store/index";

export default {
    methods: {
        alterVisibility(component) {
            var button = this.$refs[String(component)];

            store.dispatch("updateVisibilityAltered", String(component));

            this.visibility[String(component)] = !this.visibility[String(component)];

            if (this.visibility[String(component)]) {
                button.style.backgroundColor = this.colors[String(component)];
                button.style.color = "#000000";
                button.style.borderColor = "#000000";
            } else {
                button.style.backgroundColor = "#F5F5F5";
                button.style.color = "#D3D3D3";
                button.style.borderColor = "#D3D3D3";
            }
        },

        selectDeselectAll() {
            var select = this.$refs["select"];
            var label = this.$refs["label"];

            // complete this, make visibility a state variable
            if (select.checked) {
                // dispatch new visibility
                label.innerText = "De-select All";
            } else {
                // dispatch new visibility
                label.innerText = "Select All";
            }
        },
    },

    data() {
        return {
            colors: {
                SBMLDocument: "#fee090",
                Ports: "#fed9a6",
                FunctionDefinitions: "#e6f598",
                UnitDefinitions: "#f1b6da",
                Model: "#66c2a5",
                Parameters: "#fdae61",
                InitialAssignments: "#fb9a99",
                Rules: "#fb9a99",
                Compartments: "#92c5de",
                Species: "#abdda4",
                Reactions: "#a6cee3",
                Constraints: "#a6cee3",
                Events: "#fee08b",
                Objectives: "#f46d43",
                Submodels: "#d53e4f",
                GeneProducts: "#f46d43",
            },
            visibility: {
                SBMLDocument: true,
                Model: true,
                FunctionDefinitions: true,
                UnitDefinitions: true,
                Compartments: true,
                Species: true,
                Parameters: true,
                InitialAssignments: true,
                Rules: true,
                Constraints: true,
                Reactions: true,
                Objectives: true,
                Events: true,
                GeneProducts: true,
                SubModels: true,
                Ports: true,
            },
        };
    },

    computed: {
        counts() {
            console.log(store.state.counts);
            return store.state.counts;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/Filter.scss";
</style>
