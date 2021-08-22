<template>
    <div class="p-d-flex p-mt-2">
        <Tag
            :value="`type: ${parameter.type}`"
            severity="warning"
            class="qualifier"
        ></Tag>
        <Tag
            :value="`value: ${parameter.value}`"
            severity="info"
            class="resource"
        ></Tag>
    </div>
    <div
        class="p-card"
        v-if="
            parameter != null &&
            parameter.definitionURL != null &&
            parameter.math != null
        "
    >
        <span class="p-d-flex url" v-if="parameter.definitionURL != null"
            >definitionURL:
            <a href="{{ parameter.definitionURL }}">{{
                parameter.definitionURL
            }}</a></span
        >
        <span class="math" v-if="parameter.math != null">
            math: <katex :math-str="parameter.math"
        /></span>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";

import Katex from "@/components/layout/Katex.vue";

export default defineComponent({
    components: {
        Katex,
    },

    props: {
        parameter: {
            type: Object,
            default: Object,
        },
    },

    data() {
        return {
            addInfo: {},
        };
    },
});
</script>

<style lang="scss" scoped>
.qualifier {
    padding: 0 5px;
    border-radius: 5px 0 0 0px;
    width: max-content;
    border: 1px solid gray;
    border-bottom: none;
}

.resource {
    padding: 0 5px;
    border-radius: 0px 5px 0 0;
    width: max-content;
    border: 1px solid gray;
    border-bottom: none;
}

/*.url {
    background-color: aqua;
}

.math {
    background-color: rgb(13, 255, 0);
}*/

.p-card {
    box-shadow: none !important;
    border: 1px solid gray;
    border-radius: 0 5px 5px 5px;
    padding: 1px 5px;
}
</style>
