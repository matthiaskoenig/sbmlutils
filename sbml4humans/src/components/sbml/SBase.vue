<template>
    <div class="p-d-flex p-jc-between">
        <strong class="sbmlType">
            <font-awesome-icon :icon="`${icon}`" class="p-mr-1" />{{ info.sbmlType }}
        </strong>
    </div>
    <h2>{{ info.id }}</h2>
    <h3>{{ info.name }}</h3>

    <table class="table table-borderless table-sm table-condensed compact">
        <tbody>
            <!-- CORE -->
            <tr v-if="info.id != null">
                <td class="label-td"><div class="label">id</div></td>
                <td>{{ info.id }}</td>
            </tr>
            <tr v-if="info.metaId != null">
                <td class="label-td"><div class="label">metaID</div></td>
                <td>{{ info.metaId }}</td>
            </tr>
            <tr v-if="info.name != null">
                <td class="label-td"><div class="label">name</div></td>
                <td>{{ info.name }}</td>
            </tr>
            <tr v-if="info.sbo != null">
                <td class="label-td"><div class="label">sbo</div></td>
                <td>{{ info.sbo }}</td>
            </tr>
            <tr v-if="info.history != null">
                <td class="label-td"><div class="label">history</div></td>
                <td>
                    <div>
                        <div>createdDate:</div>
                        {{ info.history.createdDate }}
                        <br />
                        <div>creators:</div>
                        <ul title="Creators">
                            <li
                                v-for="creator in info.history.creators"
                                :key="creator.email"
                            >
                                {{ creator.givenName }} {{ creator.familyName }},
                                {{ creator.organization }} (<a
                                    :href="`mailto:${creator.email}`"
                                    >{{ creator.email }}</a
                                >)
                            </li>
                        </ul>
                        <div>modifiedDates:</div>
                        <ul title="Dates Modified">
                            <li v-for="date in info.history.modifiedDates" :key="date">
                                {{ date }}
                            </li>
                        </ul>
                    </div>
                </td>
            </tr>

            <!-- COMP -->
            <tr v-if="info.replacedBy != null">
                <td class="label-td"><div class="label">replacedBy</div></td>
                <td>
                    <div>submodelRef: {{ info.replacedBy.submodelRef }}</div>
                    <div>
                        replacedBySbaseref:
                        {{ info.replacedBy.replacedBySbaseref.value }}
                        (type: {{ info.replacedBy.replacedBySbaseref.type }})
                    </div>
                </td>
            </tr>
            <tr v-if="info.replacedElements != null">
                <td class="label-td"><div class="label">replacedElements</div></td>
                <td>
                    <ul title="Replaced Elements">
                        <li
                            v-for="replacedElement in info.replacedElements"
                            :key="replacedElement.submodelRef"
                        >
                            <div>
                                submodelRef:
                                <span
                                    class="links"
                                    v-on:click="
                                        openComponent(
                                            'Submodel:' + replacedElement.submodelRef
                                        )
                                    "
                                    >{{ replacedElement.submodelRef }}</span
                                >
                            </div>
                            <div>
                                replacedElementSbaseref:
                                {{ replacedElement.replacedElementSbaseref.value }}
                                (type:
                                {{ replacedElement.replacedElementSbaseref.type }})
                            </div>
                        </li>
                    </ul>
                </td>
            </tr>

            <!-- DISTRIB -->
            <tr v-if="info.uncertainties != null && info.uncertainties.length > 0">
                <td class="label-td"><div class="label">uncertainties</div></td>
                <td>
                    <ol title="Uncertainties">
                        <li
                            v-for="uncertainty in info.uncertainties"
                            :key="uncertainty"
                        >
                            Uncertainty Parameters
                            <div
                                v-for="param in uncertainty.uncertaintyParameters"
                                :key="param"
                            >
                                <UncertaintyBadge :parameter="param" />
                            </div>
                        </li>
                    </ol>
                </td>
            </tr>
        </tbody>
    </table>
</template>

<script lang="ts">
import store from "@/store/index";
import icons from "@/data/fontAwesome";
import colorScheme from "@/data/colorScheme";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "@vue/runtime-core";

import UncertaintyBadge from "@/components/sbmlmisc/UncertaintyBadge.vue";

/**
 * Component to define display of SBase information.
 */
export default defineComponent({
    components: {
        UncertaintyBadge,
    },

    props: {
        info: {
            type: Object,
            default: TYPES.SBase,
        },
        math: {
            type: String,
            default: "",
        },
    },

    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },

    computed: {
        color(): string {
            return colorScheme.componentColor[this.info.sbmlType];
        },

        icon(): string {
            return icons.icons[this.info.sbmlType];
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
