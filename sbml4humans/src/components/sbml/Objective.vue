<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.type != null">
                <td class="label-td"><div class="label">type</div></td>
                <td>{{ info.type }}</td>
            </tr>
            <tr v-if="info.fluxObjectives != null && info.fluxObjectives.length > 0">
                <td class="label-td"><div class="label">fluxObjectives</div></td>
                <td>
                    <ul title="Flux Objectives">
                        <li
                            v-for="fluxObjective in info.fluxObjectives"
                            :key="fluxObjective.reaction"
                        >
                            <div v-if="fluxObjective.reaction">
                                {{ fluxObjective.reaction }}
                            </div>
                            <div v-if="fluxObjective.sign || fluxObjective.coefficient">
                                <span v-if="fluxObjective.sign != null"
                                    >sign: {{ fluxObjective.sign }}</span
                                >
                                <span v-if="fluxObjective.coefficient != null"
                                    >, coefficient:
                                    {{ fluxObjective.coefficient }}</span
                                >
                            </div>
                        </li>
                    </ul>
                </td>
            </tr>
        </tbody>
    </table>

    <!-- <div class="data" v-if="info.type != null">
        <div class="label"><strong>type:</strong> {{ info.type }}</div>
    </div>

    <div
        class="data"
        v-if="info.fluxObjectives != null && info.fluxObjectives.length > 0"
    >
        <div class="label"><strong>fluxObjectives:</strong></div>
        <br />
        <div class="p-ml-4">
            <ul title="Flux Objectives">
                <li
                    v-for="fluxObjective in info.fluxObjectives"
                    :key="fluxObjective.reaction"
                >
                    <div v-if="fluxObjective.reaction">
                        {{ fluxObjective.reaction }}
                    </div>
                    <div v-if="fluxObjective.sign || fluxObjective.coefficient">
                        <span v-if="fluxObjective.sign != null"
                            >sign: {{ fluxObjective.sign }}</span
                        >
                        <span v-if="fluxObjective.coefficient != null"
                            >, coefficient: {{ fluxObjective.coefficient }}</span
                        >
                    </div>
                </li>
            </ul>
        </div>
    </div> -->
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
@import "@/assets/styles/scss/SBase.scss";
</style>
