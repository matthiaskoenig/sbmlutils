<template>
    <!-- Model Reference -->
    <div class="data" v-if="info.modelRef">
        <div class="label"><strong>modelRef:</strong> {{ info.modelRef }}</div>
    </div>

    <!-- Deletions -->
    <div class="data" v-if="info.deletions && info.deletions[0].type">
        <div class="label"><strong>deletions:</strong></div>
        <br />
        <div class="ml-4">
            <ul title="Deletions">
                <li v-for="deletion in info.deletions" v-bind:key="deletion.value">
                    type: {{ deletion.type }}, value: {{ deletion.value }}
                </li>
            </ul>
        </div>
    </div>

    <!-- Time Conversion -->
    <div class="data" v-if="info.timeConversion">
        <div class="label">
            <strong>timeConversion:</strong> {{ info.timeConversion }}
        </div>
    </div>

    <!-- Extent Conversion -->
    <div class="data" v-if="info.extentConversion">
        <div class="label">
            <strong>extentConversion:</strong> {{ info.extentConversion }}
        </div>
    </div>
</template>

<script>
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

/**
 * Component to define display of Submodel objects.
 */
export default defineComponent({
    props: {
        info: {
            type: Object,
            default: TYPES.Submodel,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/components/sbml/Compartment.scss";
</style>
