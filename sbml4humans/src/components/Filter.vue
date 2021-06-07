<template>
    <div class="filter">
        <div class="tag-list">
            <div class="selector">
                <button
                    ref="SBMLDocument"
                    class="tag btn btn-outline"
                    @click="alterVisibility('SBMLDocument')"
                    :style="`background-color: ${colors.SBMLDocument}`"
                >
                    SBML Document
                </button>
            </div>

            <div class="selector">
                <button
                    ref="Ports"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Port')"
                    :style="`background-color: ${colors.Ports}`"
                >
                    Ports
                </button>
            </div>

            <div class="selector">
                <button
                    ref="Model"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Model')"
                    :style="`background-color: ${colors.Model}`"
                >
                    Models
                </button>
            </div>

            <div class="selector">
                <button
                    ref="FunctionDefinitions"
                    class="tag btn btn-outline"
                    @click="alterVisibility('FunctionDefinitions')"
                    :style="`background-color: ${colors.FunctionDefinitions}`"
                >
                    Function Definitions
                </button>
            </div>

            <div class="selector">
                <button
                    ref="UnitDefinitions"
                    class="tag btn btn-outline"
                    @click="alterVisibility('UnitDefinitions')"
                    :style="`background-color: ${colors.UnitDefinitions}`"
                >
                    Unit Definitions
                </button>
            </div>

            <div class="selector">
                <button
                    ref="Compartments"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Compartments')"
                    :style="`background-color: ${colors.Compartments}`"
                >
                    Compartments
                </button>
            </div>

            <div class="selector">
                <button
                    ref="Species"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Species')"
                    :style="`background-color: ${colors.Species}`"
                >
                    Species
                </button>
            </div>

            <div class="selector">
                <button
                    ref="Parameters"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Parameters')"
                    :style="`background-color: ${colors.Parameters}`"
                >
                    Parameters
                </button>
            </div>

            <div class="selector">
                <button
                    ref="Reactions"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Reactions')"
                    :style="`background-color: ${colors.Reactions}`"
                >
                    Reactions
                </button>
            </div>

            <div class="selector">
                <button
                    ref="AssignmentRules"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Rules')"
                    :style="`background-color: ${colors.AssignmentRules}`"
                >
                    Rules
                </button>
            </div>

            <div class="selector">
                <button
                    ref="Constraints"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Constraints')"
                    :style="`background-color: ${colors.Constraints}`"
                >
                    Constraints
                </button>
            </div>

            <div class="selector">
                <button
                    ref="InitialAssignments"
                    class="tag btn btn-outline"
                    @click="alterVisibility('InitialAssignments')"
                    :style="`background-color: ${colors.InitialAssignments}`"
                >
                    Initial Assignments
                </button>
            </div>

            <div class="selector">
                <button
                    ref="Events"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Events')"
                    :style="`background-color: ${colors.Events}`"
                >
                    Events
                </button>
            </div>
        </div>
    </div>
</template>

<script>
import store from "@/store/index";

export default {
    methods: {
        alterVisibility(component) {
            var button = this.$refs[String(component)];
            console.log(button);

            store.dispatch("updateVisibilityAltered", String(component));

            this.visibility[String(component)] = !this.visibility[String(component)];

            console.log(this.visibility[String(component)]);
            if (this.visibility[String(component)]) {
                console.log(this.colors[String(component)]);
                button.style.backgroundColor = this.colors[String(component)];
            } else {
                console.log("transparent");
                button.style.backgroundColor = "#ffffff00";
            }
        },
    },

    data() {
        return {
            count: {
                SBMLDocument: {
                    original: 6,
                    current: 6,
                },
                Model: {
                    original: 6,
                    current: 6,
                },
                FunctionDefinitions: {
                    original: 6,
                    current: 6,
                },
                UnitDefinitions: {
                    original: 6,
                    current: 6,
                },
                Compartments: {
                    original: 6,
                    current: 6,
                },
                Species: {
                    original: 6,
                    current: 6,
                },
                Parameters: {
                    original: 6,
                    current: 6,
                },
                InitialAssignments: {
                    original: 6,
                    current: 6,
                },
                Rules: {
                    original: 6,
                    current: 6,
                },
                Constraints: {
                    original: 6,
                    current: 6,
                },
                Reactions: {
                    original: 6,
                    current: 6,
                },
                Objectives: {
                    original: 6,
                    current: 6,
                },
                Events: {
                    original: 6,
                    current: 6,
                },
                GeneProducts: {
                    original: 6,
                    current: 6,
                },
                SubModels: {
                    original: 6,
                    current: 6,
                },
                Ports: {
                    original: 6,
                    current: 6,
                },
            },
            colors: {
                SBMLDocument: "#fee090",
                Ports: "#fed9a6",
                FunctionDefinitions: "#e6f598",
                UnitDefinitions: "#f1b6da",
                Model: "#66c2a5",
                Parameters: "#fdae61",
                InitialAssignments: "#fb9a99",
                AssignmentRules: "#fb9a99",
                Compartments: "#92c5de",
                Species: "#abdda4",
                Reactions: "#a6cee3",
                Constraints: "#a6cee3",
                Events: "#fee08b",
                Objectives: "#f46d43",
                Defaults: "#d53e4f",
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
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/Filter.scss";
</style>
