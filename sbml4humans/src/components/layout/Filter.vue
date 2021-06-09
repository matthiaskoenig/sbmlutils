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
            <sup v-if="counts.SBMLDocument > 0">
                <div ref="SBMLDocumentBadge" class="badge">{{
                    counts.SBMLDocument
                }}</div>
            </sup>

            <div class="selector">
                <button
                    ref="Ports"
                    v-if="counts.Ports > 0"
                    class="tag btn btn-outline"
                    @click="alterVisibility('Ports')"
                    :style="`background-color: ${colors.Ports}`"
                >
                    Ports
                </button>
            </div>
            <sup v-if="counts.Ports > 0">
                <div ref="PortsBadge" class="badge">{{ counts.Ports }}</div>
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
            <sup v-if="counts.Model > 0">
                <div ref="ModelBadge" class="badge">{{ counts.Model }}</div>
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
            <sup v-if="counts.FunctionDefinitions > 0">
                <div ref="FunctionDefinitionsBadge" class="badge">{{
                    counts.FunctionDefinitions
                }}</div>
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
            <sup v-if="counts.UnitDefinitions > 0">
                <div ref="UnitDefinitionsBadge" class="badge">{{
                    counts.UnitDefinitions
                }}</div>
            </sup>

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
            <sup v-if="counts.Compartments > 0">
                <div ref="CompartmentsBadge" class="badge">{{
                    counts.Compartments
                }}</div>
            </sup>

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
            <sup v-if="counts.Species > 0">
                <div ref="SpeciesBadge" class="badge">{{ counts.Species }}</div>
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
            <sup v-if="counts.Parameters > 0">
                <div ref="ParametersBadge" class="badge">{{
                    counts.Parameters
                }}</div>
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
            <sup v-if="counts.Reactions > 0">
                <div ref="ReactionsBadge" class="badge">{{ counts.Reactions }}</div>
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
            <sup v-if="counts.Rules > 0">
                <div ref="RulesBadge" class="badge">{{ counts.Rules }}</div>
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
            <sup v-if="counts.Constraints > 0">
                <div ref="ConstraintsBadge" class="badge">{{
                    counts.Constraints
                }}</div>
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
            <sup v-if="counts.InitialAssignments > 0">
                <div ref="InitialAssignmentsBadge" class="badge">{{
                    counts.InitialAssignments
                }}</div>
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
            <sup v-if="counts.Events > 0">
                <div ref="EventsBadge" class="badge">{{ counts.Events }}</div>
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
            <sup v-if="counts.Objectives > 0">
                <div ref="ObjectivesBadge" class="badge">{{
                    counts.Objectives
                }}</div>
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
            <sup v-if="counts.Submodels > 0">
                <div ref="SubmodelsBadge" class="badge">{{ counts.Submodels }}</div>
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
            <sup v-if="counts.GeneProducts > 0">
                <div ref="GeneProductsBadge" class="badge">{{
                    counts.GeneProducts
                }}</div>
            </sup>

            <div class="master-select">
                <input ref="select" class="tick" type="radio" @click="selectAll()" />
                <div class="label">Select All</div>

                <input
                    ref="de-select"
                    class="tick ml-4"
                    type="radio"
                    @click="deSelectAll()"
                />
                <div class="label">De-Select All</div>
            </div>
        </div>
    </div>
</template>

<script>
import store from "@/store/index";

export default {
    methods: {
        changeButtonShade(component, active) {
            console.log(component);
            var button = this.$refs[component];
            var badge = this.$refs[String(component) + "Badge"];

            if (active === true) {
                button.style.backgroundColor = this.colors[component];
                button.style.color = "#000000";
                button.style.borderColor = "#000000";

                badge.style.backgroundColor = "#000000";
                badge.style.color = "#FFFFFF";
                badge.style.borderColor = "#000000";
            } else {
                button.style.backgroundColor = "#F5F5F5";
                button.style.color = "#D3D3D3";
                button.style.borderColor = "#D3D3D3";

                badge.style.backgroundColor = "#F5F5F5";
                badge.style.color = "#A9A9A9";
                badge.style.borderColor = "#A9A9A9";
            }
        },

        alterVisibility(component) {
            var currVisibility = this.visibility;
            // update the visibility of the specific component
            currVisibility[String(component)] = !currVisibility[String(component)];

            store.dispatch("updateVisibility", currVisibility);

            if (this.visibility[String(component)] === true) {
                this.changeButtonShade(String(component), true);
            } else {
                this.changeButtonShade(String(component), false);
            }
        },

        selectAll() {
            var deSelect = this.$refs["de-select"];

            var currVisibility = this.visibility;
            // make visibility of all SBML components "true"
            for (let component in currVisibility) {
                currVisibility[String(component)] = true;
                if (this.counts[String(component)] > 0) {
                    this.changeButtonShade(String(component), true);
                }
            }

            store.dispatch("updateVisibility", currVisibility);

            deSelect.checked = false;
        },

        deSelectAll() {
            var select = this.$refs["select"];

            var currVisibility = this.visibility;
            // make visibility of all SBML components "false"
            for (let component in currVisibility) {
                currVisibility[String(component)] = false;
                if (this.counts[String(component)] > 0) {
                    this.changeButtonShade(String(component), false);
                }
            }

            store.dispatch("updateVisibility", currVisibility);

            select.checked = false;
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
        };
    },

    computed: {
        counts() {
            return store.state.counts;
        },

        visibility() {
            return store.state.visibility;
        },
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/layout/Filter.scss";
</style>
