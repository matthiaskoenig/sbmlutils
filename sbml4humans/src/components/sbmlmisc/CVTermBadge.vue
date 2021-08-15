<template>
    <div class="p-d-flex">
        <div class="badge badge-success qualifier">{{ qualifier }}</div>
        <a :href="resource" target="_blank" class="badge badge-warning resource">{{
            resource
        }}</a>
    </div>
    <div class="p-mt-1 p-mb-2 p-ml-2" v-if="addInfo != null">
        <strong>{{ addInfo.name }}:</strong> {{ addInfo.definition }} <br />
        <span v-if="addInfo.synonyms != null"
            >Synonyms: {{ addInfo.synonyms.join() }}</span
        >
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import additionalInfoUtils from "@/helpers/additionalInfoUtils";

export default defineComponent({
    props: {
        qualifier: {
            type: String,
            default: "",
        },
        resource: {
            type: String,
            default: "",
        },
    },

    data() {
        return {
            addInfo: {},
        };
    },

    created() {
        const parts = this.resource.split("/");
        const resourceID = parts[parts.length - 1];
        additionalInfoUtils.fetchAdditionalInfo(resourceID).then((res) => {
            console.log(res);
            this.addInfo = res as Record<string, unknown>;
        });
    },
});
</script>

<style lang="scss" scoped>
.qualifier {
    border-radius: 5px 0 0 5px;
}

.resource {
    border-radius: 0px 5px 5px 0;
}
</style>
