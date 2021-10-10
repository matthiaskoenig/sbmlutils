<template>
    <div class="p-ml-2 p-mt-4 menuheader">OMEX TREE</div>
    <Tree :value="nodes.root" style="background-color: #ffffff00; border: none; width: max-content">
        <template #default="slotProps">
            <!--<font-awesome-icon
                icon="file-code"
                :fixedWidth="true"
                :border="false"
                size="1x"
            ></font-awesome-icon>-->
            <div
                v-if="slotProps.node.type === 'sbml'"
                @click="changeReport(slotProps.node.data)"
                class="sbml-object"
            >
                <b>{{ slotProps.node.label }}</b>
            </div>
            <div v-else>
                <b>{{ slotProps.node.label }}</b>
            </div>
        </template>
    </Tree>
</template>

<script lang="ts">
import { defineComponent } from "@vue/runtime-core";
import store from "@/store/index";

export default defineComponent({
    data() {
        return {
            nodes: JSON.parse(JSON.stringify(store.state.OMEXTree)),
        };
    },

    mounted() {
        console.log(JSON.parse(JSON.stringify(store.state.OMEXTree)));
    },

    methods: {
        changeReport(location: string) {
            console.log("Bruh moment");
            const requiredContext = JSON.parse(JSON.stringify(store.state.contexts))[location];
            store.dispatch("updateReportStatesAndFollowUp", requiredContext);
        },
    },
});
</script>

<style lang="scss">
.sbml-object:hover {
    cursor: pointer;
}
</style>
