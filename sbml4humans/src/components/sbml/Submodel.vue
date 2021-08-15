<template>
    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <tr v-if="info.modelRef != null">
                <td class="label-td"><div class="label">modelRef</div></td>
                <td>{{ info.modelRef }}</td>
            </tr>
            <tr v-if="info.deletions != null && info.deletions[0].type">
                <td class="label-td"><div class="label">deletions</div></td>
                <td>
                    <ul title="Deletions">
                        <li v-for="deletion in info.deletions" :key="deletion.value">
                            type: {{ deletion.type }}, value: {{ deletion.value }}
                        </li>
                    </ul>
                </td>
            </tr>
            <tr v-if="info.timeConversion != null">
                <td class="label-td"><div class="label">timeConversion</div></td>
                <td>{{ info.timeConversion }}</td>
            </tr>
            <tr v-if="info.extentConversion != null">
                <td class="label-td"><div class="label">extentConversion</div></td>
                <td>{{ info.extentConversion }}</td>
            </tr>
        </tbody>
    </table>

    <!-- <div class="data" v-if="info.modelRef != null">
        <div class="label"><strong>modelRef:</strong> {{ info.modelRef }}</div>
    </div>

    <div class="data" v-if="info.deletions != null && info.deletions[0].type">
        <div class="label"><strong>deletions:</strong></div>
        <br />
        <div class="p-ml-4">
            <ul title="Deletions">
                <li v-for="deletion in info.deletions" :key="deletion.value">
                    type: {{ deletion.type }}, value: {{ deletion.value }}
                </li>
            </ul>
        </div>
    </div>

    <div class="data" v-if="info.timeConversion != null">
        <div class="label">
            <strong>timeConversion:</strong> {{ info.timeConversion }}
        </div>
    </div>

    <div class="data" v-if="info.extentConversion != null">
        <div class="label">
            <strong>extentConversion:</strong> {{ info.extentConversion }}
        </div>
    </div> -->
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
@import "@/assets/styles/scss/SBase.scss";
</style>
