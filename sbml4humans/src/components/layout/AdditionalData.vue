<template>
    <div class="p-ml-1">
        <div v-if="info.cvterms != null">
            <div class="label">cvterms</div>
            <div class="p-ml-1">
                <div v-for="cvterm in info.cvterms" :key="cvterm.qualifier">
                    <CVTermBadge
                        v-for="resource in cvterm.resources"
                        :key="resource"
                        :qualifier="cvterm.qualifier"
                        :resource="resource"
                    />
                </div>
            </div>
        </div>

        <div v-if="info.notes != null">
            <div class="label">notes</div>
            <hr />
            <div class="p-ml-1" v-html="info.notes"></div>
            <hr />
        </div>

        <CodeContainer :info="info" />
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";

import CVTermBadge from "@/components/sbmlmisc/CVTermBadge.vue";
import CodeContainer from "@/components/layout/CodeContainer.vue";

export default defineComponent({
    components: {
        CVTermBadge,
        CodeContainer,
    },

    props: {
        info: {
            type: Object,
        },
    },
});
</script>

<style lang="scss" scoped>
@import "@/assets/styles/scss/SBase.scss";
</style>
