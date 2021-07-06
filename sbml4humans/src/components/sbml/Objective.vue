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

<script lang="ts">
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Objective objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.Objective,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/SBase.scss";
</style>
