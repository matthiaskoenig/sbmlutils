<template>
    <div class="ml-1">
        <div class="mb-3" v-if="info.cvterms != null">
            <div class="label"><strong>cvterms</strong></div>
            <div class="ml-4">
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
