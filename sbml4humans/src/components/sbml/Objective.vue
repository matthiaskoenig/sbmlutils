<template>
    <!-- Type -->
    <div class="data" v-if="info.type">
        <div class="label"><strong>type:</strong> {{ info.type }}</div>
    </div>

    <!-- Flux Objectives -->
    <div class="data" v-if="info.fluxObjectives.length > 0">
        <div class="label"><strong>fluxObjectives:</strong></div>
        <br />
        <div class="ml-4">
            <ul title="Flux Objectives">
                <li
                    v-for="fluxObjective in info.fluxObjectives"
                    v-bind:key="fluxObjective.reaction"
                >
                    <div v-if="fluxObjective.reaction">
                        {{ fluxObjective.reaction }}
                    </div>
                    <div v-if="fluxObjective.sign || fluxObjective.coefficient">
                        <span v-if="fluxObjective.sign"
                            >sign: {{ fluxObjective.sign }}</span
                        >
                        <span v-if="fluxObjective.coefficient"
                            >, coefficient: {{ fluxObjective.coefficient }}</span
                        >
                    </div>
                </li>
            </ul>
        </div>
    </div>
</template>

<script>
import TYPES from "@/sbmlComponents";

export default {
    props: {
        info: TYPES.Objective,
    },

    data() {
        return {};
    },
};
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
