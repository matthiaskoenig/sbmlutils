<template>
    <div class="holder">
        <!--        <div class="selector"/>-->
        <!--        <div-->
        <!--            class="clickable"-->
        <!--            v-on:click="focusTable(item.sbmlType)"-->
        <!--            v-if="item.count"-->
        <!--        >-->
        <!--             <span :style="`color: ${item.color}`">-->
        <!--            <font-awesome-icon-->
        <!--                :icon="item.icon"-->
        <!--                :fixedWidth="true"-->
        <!--                :border="false"-->
        <!--                size="1x"-->
        <!--                class="p-mr-2"-->
        <!--            ></font-awesome-icon>-->
        <!--             </span>-->
        <!--            <span class="p-mr-2">-->
        <!--                <strong>{{ item.sbmlType }}</strong> ({{item.count}})-->
        <!--            </span>-->
        <!--        </div>-->

        <div class="selector" />
        <div
            class="p-card p-d-flex p-flex-column"
            v-on:click="showDetail"
            title="Show details"
        >
            <div
                class="p-d-flex p-jc-between p-pl-2 p-pr-1"
                :style="`background-color: ${color}`"
            >
                <div class="p-mr-3" style="word-break: break-all">
                    <strong>{{ info.id }}</strong>
                </div>
                <div class="p-d-flex">
                    <strong>{{ sbmlType }}</strong>
                    <font-awesome-icon :icon="`${icon}`" class="p-ml-2 p-mt-1" />
                </div>
            </div>
            <div v-if="info.metaId || info.sbo" class="p-px-2">
                <div class="p-d-flex p-jc-between">
                    <span class="text-primary" v-if="info.metaId">
                        metaId:
                        <span v-if="info.metaId.length < 20">{{ info.metaId }}</span>
                        <span v-else>{{ info.metaId.substring(0, 20) + "..." }}</span>
                    </span>
                    <span v-if="info.sbo">{{ info.sbo }}</span>
                </div>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import colors from "@/data/colorScheme";
import icons from "@/data/fontAwesome";
import store from "@/store/index";
import TYPES from "@/data/sbmlComponents";
import { defineComponent } from "vue";

/**
 * Component to display meta data about an SBML objects.
 */
export default defineComponent({
    props: {
        sbmlType: {
            type: String,
            default: "SBMLDocument",
        },
        info: {
            type: Object,
            default: TYPES.SBMLDocument,
        },
    },

    data(): Record<string, unknown> {
        return {
            color: {
                type: String,
                default: "#FFFFFF",
            },
        };
    },

    mounted(): void {
        this.color = colors.componentColor[this.sbmlType];
    },

    computed: {
        /**
         * Reactively returns the visibility of SBML components from Vuex state/localStorage.
         */
        visibility(): Record<string, unknown> {
            return store.state.visibility;
        },

        icon(): string {
            return icons.icons[this.sbmlType];
        },
    },

    methods: {
        /**
         * Updates the detailInfo in Vuex state/localStorage to this SBML component's info.
         */
        showDetail(): void {
            if (this.sbmlType != "SBMLDocument") {
                store.dispatch("updateCurrentModel", this.info.pk);
            }
            store.dispatch("initializeHistoryStack", this.info.pk);
        },
    },
});
</script>

<style lang="scss" scoped></style>
