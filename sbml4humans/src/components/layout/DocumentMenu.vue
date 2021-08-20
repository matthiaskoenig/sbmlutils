<template>
    <div>
        <h3>Document & Models</h3>

        <SBMLObject
            v-for="component in coreComponents"
            :key="component.pk"
            :sbmlType="component.sbmlType"
            :info="component"
        />
    </div>
</template>

<script lang="ts">
import store from "@/store";
import { defineComponent } from "@vue/runtime-core";
import SBMLObject from "@/components/layout/SBMLObject.vue";

export default defineComponent({
    components: {
        SBMLObject,
    },
    computed: {
        coreComponents(): Array<Record<string, unknown>> {
            return store.getters.reportBasics;
        },
    },
});
</script>

<style lang="scss" scoped></style>
