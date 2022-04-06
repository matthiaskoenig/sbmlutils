<template>
    <div class="p-ml-2 p-mt-1 menuheader">OMEX</div>
    <Tree
        :value="nodes.root"
        style="background-color: #ffffff00; border: none; width: max-content"
        :expandedKeys="expandedKeys"
    >
        <template #default="slotProps">
            <div
                v-if="slotProps.node.type === 'sbml'"
                @click="changeReport(slotProps.node.data)"
                class="sbml-object"
                :style="`color: ${
                    activePath.includes(slotProps.node.key) ? '#66c2a5' : '#000000'
                }`"
            >
                <!--<font-awesome-icon
                    icon="file-code"
                    :fixedWidth="true"
                    :border="false"
                    size="1x"
                    style="color: #66c2a5"
                ></font-awesome-icon>-->
                <img
                    src="@/assets/images/sbml-icon.png"
                    width="15"
                    height="15"
                    class="p-mr-2"
                />
                <b>{{ slotProps.node.label }}</b>
            </div>
            <div
                v-else
                :style="`color: ${
                    activePath.includes(slotProps.node.key) ? '#66c2a5' : '#000000'
                }`"
            >
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
            expandedKeys: {},
        };
    },

    mounted() {
        //console.log(JSON.parse(JSON.stringify(store.state.OMEXTree)));
        this.highlightPath();
    },

    computed: {
        activePath() {
            const currentDocumentPath = JSON.parse(
                JSON.stringify(store.state.currentDocumentLocation)
            );
            const tokens = currentDocumentPath.split("/");
            return tokens;
        },
    },

    methods: {
        changeReport(location: string) {
            const requiredContext = JSON.parse(JSON.stringify(store.state.contexts))[
                location
            ];
            store.dispatch("updateReportStatesAndFollowUp", requiredContext);
            store.dispatch("updateCurrentDocumentLocation", location);
            this.highlightPath();
        },

        highlightPath() {
            this.expandedKeys = {};
            const tokens = this.activePath;
            for (let i in tokens) {
                this.expandedKeys[tokens[i]] = true;
            }
        },
    },
});
</script>

<style lang="scss">
.sbml-object {
    display: flex;
    align-items: center;
}

.sbml-object:hover {
    cursor: pointer;
}
</style>
